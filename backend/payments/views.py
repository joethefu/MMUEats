import logging

from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from common.utils import write_audit_log
from orders.models import Order
from . import mpesa_service
from .models import Payment
from .serializers import PaymentSerializer, STKPushRequestSerializer

logger = logging.getLogger("django")


class MyPaymentsViewSet(viewsets.ReadOnlyModelViewSet):
    """Spec §37: payment history, scoped to the logged-in customer's own orders."""

    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin":
            return Payment.objects.all()
        return Payment.objects.filter(order__customer=user)


class MpesaSTKPushView(APIView):
    """
    Spec §37: initiates Lipa Na M-Pesa Online (STK Push) for an order already
    created with payment_method='mpesa'. Safe to call again if the first push
    timed out or was cancelled on the customer's phone.
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "mpesa-stk"

    def post(self, request):
        serializer = STKPushRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order_id = serializer.validated_data["order_id"]
        phone_number = serializer.validated_data["phone_number"]

        try:
            order = Order.objects.select_related("payment").get(pk=order_id, customer=request.user)
        except Order.DoesNotExist:
            return Response({"error": {"code": "not_found", "message": "Order not found."}}, status=404)

        if order.payment_method != Order.PaymentMethod.MPESA:
            return Response(
                {"error": {"code": "invalid_method", "message": "This order isn't set up for M-Pesa payment."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment = getattr(order, "payment", None)
        if payment is None:
            payment = Payment.objects.create(order=order, method=Order.PaymentMethod.MPESA, amount=order.total)

        if payment.status == Payment.Status.PAID:
            return Response(
                {"error": {"code": "already_paid", "message": "This order has already been paid for."}},
                status=status.HTTP_409_CONFLICT,
            )

        try:
            result = mpesa_service.stk_push(
                phone_number=phone_number,
                amount=order.total,
                account_reference=order.order_number,
                transaction_desc=f"MMUEats order {order.order_number}",
            )
        except Exception as exc:
            logger.exception("M-Pesa STK push failed for order %s: %s", order.order_number, exc)
            payment.status = Payment.Status.FAILED
            payment.result_desc = "Could not reach M-Pesa. Please try again."
            payment.save()
            return Response(
                {"error": {"code": "mpesa_error", "message": "Could not initiate M-Pesa payment. Please try again."}},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        payment.phone_number = phone_number
        payment.merchant_request_id = result["merchant_request_id"]
        payment.checkout_request_id = result["checkout_request_id"]
        payment.status = Payment.Status.PROCESSING
        payment.is_mocked = result["is_mocked"]
        payment.save()

        response_data = {
            "success": True,
            "message": "Check your phone to complete the M-Pesa payment.",
            "payment": PaymentSerializer(payment).data,
        }
        if result["is_mocked"]:
            # Dev-mode convenience: no real Safaricom sandbox is reachable from here,
            # so tell the frontend it can hit the simulate-callback endpoint.
            response_data["dev_note"] = (
                "M-Pesa credentials aren't configured — this is a mocked STK push. "
                "Call /api/payments/mpesa/simulate/ to simulate the customer completing payment."
            )
        return Response(response_data)


def _process_stk_callback(callback_body):
    """Shared logic for both the real Safaricom callback and the dev simulate endpoint."""
    try:
        callback = callback_body["Body"]["stkCallback"]
        checkout_request_id = callback["CheckoutRequestID"]
        result_code = callback["ResultCode"]
        result_desc = callback.get("ResultDesc", "")
    except (KeyError, TypeError):
        logger.warning("Malformed M-Pesa callback received: %s", callback_body)
        return {"ResultCode": 0, "ResultDesc": "Accepted"}

    try:
        payment = Payment.objects.select_related("order").get(checkout_request_id=checkout_request_id)
    except Payment.DoesNotExist:
        logger.warning("M-Pesa callback for unknown CheckoutRequestID: %s", checkout_request_id)
        return {"ResultCode": 0, "ResultDesc": "Accepted"}

    payment.raw_callback = callback_body
    payment.result_code = result_code
    payment.result_desc = result_desc

    if result_code == 0:
        metadata_items = callback.get("CallbackMetadata", {}).get("Item", [])
        metadata = {item["Name"]: item.get("Value") for item in metadata_items}
        payment.mpesa_receipt_number = metadata.get("MpesaReceiptNumber", "")
        payment.status = Payment.Status.PAID
        payment.transaction_date = timezone.now()
        payment.order.payment_status = Order.PaymentStatus.PAID
        payment.order.save(update_fields=["payment_status"])
    else:
        payment.status = Payment.Status.FAILED

    payment.save()
    write_audit_log(None, f"mpesa_callback_{payment.status}", obj=payment.order)
    return {"ResultCode": 0, "ResultDesc": "Accepted"}


class MpesaCallbackView(APIView):
    """
    Safaricom calls this URL directly (MPESA_CALLBACK_URL) once the customer
    completes or cancels the STK push on their phone. No authentication —
    Safaricom is not a logged-in user — so validate strictly on payload shape.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        return Response(_process_stk_callback(request.data))


class SimulateMpesaCallbackView(APIView):
    """
    DEV-ONLY convenience endpoint: manually trigger the same effect as a real
    Safaricom callback. Safe by construction rather than by environment flag —
    it only ever acts on a Payment whose `is_mocked=True`, and a payment can
    only be mocked when MPESA_CONSUMER_KEY/SECRET/PASSKEY are unset, which is
    never true in a correctly configured production deployment.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_id = request.data.get("order_id")
        success_raw = request.data.get("success", True)
        success = success_raw if isinstance(success_raw, bool) else str(success_raw).strip().lower() not in ("false", "0", "")

        try:
            payment = Payment.objects.select_related("order").get(order_id=order_id, order__customer=request.user)
        except Payment.DoesNotExist:
            return Response({"error": {"code": "not_found", "message": "Payment not found."}}, status=404)

        if not payment.is_mocked:
            return Response(
                {"error": {"code": "not_mocked", "message": "This payment used real M-Pesa credentials — simulate isn't available."}},
                status=400,
            )

        callback_payload = mpesa_service.simulate_mock_callback_payload(
            payment.checkout_request_id, payment.merchant_request_id, payment.amount, payment.phone_number, success=success
        )
        result = _process_stk_callback(callback_payload)
        payment.refresh_from_db()
        return Response({"success": True, "callback_result": result, "payment": PaymentSerializer(payment).data})

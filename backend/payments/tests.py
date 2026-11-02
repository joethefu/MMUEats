from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from meals.models import Meal
from restaurants.models import Restaurant
from users.models import User

from .models import Payment


def make_customer(email="cust@gmail.com"):
    user = User.objects.create_user(email=email, password="Pass12345", full_name="Customer")
    user.is_email_verified = True
    user.save()
    return user


def make_vendor_with_restaurant(email="vendor@x.com"):
    vendor = User.objects.create_user(email=email, password="Pass12345", full_name="Vendor", role=User.Role.VENDOR)
    vendor.is_approved = True
    vendor.is_email_verified = True
    vendor.save()
    restaurant = Restaurant.objects.create(
        owner=vendor, name="Pay Kitchen", slug=f"pay-{vendor.id}", location="Loc",
        status="open", is_active=True, delivery_fee=Decimal("50.00"),
    )
    return vendor, restaurant


def checkout_order(client, customer, restaurant, payment_method="cash_on_delivery"):
    meal = Meal.objects.create(restaurant=restaurant, name="Pay Meal", price=Decimal("200.00"))
    client.force_authenticate(user=customer)
    client.post(reverse("orders:cart"), {"meal_id": str(meal.id), "quantity": 1})
    resp = client.post(reverse("orders:checkout"), {
        "delivery_campus_location": "Hostel A", "payment_method": payment_method,
    })
    return resp.data["id"]


class CheckoutPaymentCreationTests(APITestCase):
    def setUp(self):
        self.customer = make_customer()
        self.vendor, self.restaurant = make_vendor_with_restaurant()

    def test_checkout_creates_pending_payment_record(self):
        order_id = checkout_order(self.client, self.customer, self.restaurant, "cash_on_delivery")
        payment = Payment.objects.get(order_id=order_id)
        self.assertEqual(payment.status, Payment.Status.PENDING)
        self.assertEqual(payment.method, "cash_on_delivery")
        self.assertEqual(payment.amount, Decimal("250.00"))  # 200 meal + 50 delivery

    def test_cod_payment_marked_paid_on_delivery(self):
        order_id = checkout_order(self.client, self.customer, self.restaurant, "cash_on_delivery")
        self.client.force_authenticate(user=self.vendor)
        status_url = lambda: reverse("orders:order-update-status", args=[order_id])
        self.client.post(status_url(), {"status": "accepted"})
        self.client.post(status_url(), {"status": "preparing"})
        self.client.post(status_url(), {"status": "ready_for_pickup"})

        from deliveries.models import Delivery
        delivery = Delivery.objects.get(order_id=order_id)
        partner = User.objects.create_user(email="rider@x.com", password="Pass12345", full_name="Rider", role=User.Role.DELIVERY_PARTNER)
        partner.is_approved = True
        partner.save()
        self.client.force_authenticate(user=partner)
        self.client.post(reverse("deliveries:my-delivery-accept", args=[delivery.pk]))
        self.client.post(status_url(), {"status": "picked_up"})
        self.client.post(status_url(), {"status": "out_for_delivery"})
        self.client.post(status_url(), {"status": "delivered"})

        payment = Payment.objects.get(order_id=order_id)
        self.assertEqual(payment.status, Payment.Status.PAID)


class MpesaMockFlowTests(APITestCase):
    """
    No M-Pesa credentials are configured in the test environment, so these
    exercise the mock path — the same code path real deployments fall through
    to if Safaricom is briefly unreachable never happens, but the mock branch
    itself (used until real credentials are supplied) is fully covered here.
    """

    def setUp(self):
        self.customer = make_customer()
        self.vendor, self.restaurant = make_vendor_with_restaurant()
        self.order_id = checkout_order(self.client, self.customer, self.restaurant, "mpesa")

    def test_stk_push_returns_mocked_response(self):
        url = reverse("payments:mpesa-stk-push")
        response = self.client.post(url, {"order_id": self.order_id, "phone_number": "254712345678"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["payment"]["is_mocked"])
        self.assertIn("dev_note", response.data)

        payment = Payment.objects.get(order_id=self.order_id)
        self.assertEqual(payment.status, Payment.Status.PROCESSING)
        self.assertTrue(payment.checkout_request_id.startswith("mock-checkout-"))

    def test_stk_push_rejects_invalid_phone_format(self):
        url = reverse("payments:mpesa-stk-push")
        response = self.client.post(url, {"order_id": self.order_id, "phone_number": "0712345678"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_stk_push_rejects_wrong_payment_method_order(self):
        cod_order_id = checkout_order(self.client, self.customer, self.restaurant, "cash_on_delivery")
        url = reverse("payments:mpesa-stk-push")
        response = self.client.post(url, {"order_id": cod_order_id, "phone_number": "254712345678"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "invalid_method")

    def test_simulate_callback_success_marks_payment_paid(self):
        self.client.post(reverse("payments:mpesa-stk-push"), {"order_id": self.order_id, "phone_number": "254712345678"})
        response = self.client.post(reverse("payments:mpesa-simulate"), {"order_id": self.order_id, "success": True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        payment = Payment.objects.get(order_id=self.order_id)
        self.assertEqual(payment.status, Payment.Status.PAID)
        self.assertTrue(payment.mpesa_receipt_number.startswith("MOCK"))

        payment.order.refresh_from_db()
        self.assertEqual(payment.order.payment_status, "paid")

    def test_simulate_callback_failure_marks_payment_failed(self):
        self.client.post(reverse("payments:mpesa-stk-push"), {"order_id": self.order_id, "phone_number": "254712345678"})
        response = self.client.post(reverse("payments:mpesa-simulate"), {"order_id": self.order_id, "success": False})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        payment = Payment.objects.get(order_id=self.order_id)
        self.assertEqual(payment.status, Payment.Status.FAILED)

    def test_real_shaped_callback_hits_public_endpoint_without_auth(self):
        self.client.post(reverse("payments:mpesa-stk-push"), {"order_id": self.order_id, "phone_number": "254712345678"})
        payment = Payment.objects.get(order_id=self.order_id)

        self.client.force_authenticate(user=None)  # simulate Safaricom's unauthenticated call
        callback_body = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": payment.merchant_request_id,
                    "CheckoutRequestID": payment.checkout_request_id,
                    "ResultCode": 0,
                    "ResultDesc": "Success",
                    "CallbackMetadata": {
                        "Item": [
                            {"Name": "Amount", "Value": 250.0},
                            {"Name": "MpesaReceiptNumber", "Value": "REAL123XYZ"},
                            {"Name": "TransactionDate", "Value": 20260101120000},
                            {"Name": "PhoneNumber", "Value": 254712345678},
                        ]
                    },
                }
            }
        }
        response = self.client.post(reverse("payments:mpesa-callback"), callback_body, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.PAID)
        self.assertEqual(payment.mpesa_receipt_number, "REAL123XYZ")

    def test_malformed_callback_does_not_500(self):
        response = self.client.post(reverse("payments:mpesa-callback"), {"garbage": True}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PaymentHistoryTests(APITestCase):
    def setUp(self):
        self.customer = make_customer()
        self.vendor, self.restaurant = make_vendor_with_restaurant()

    def test_customer_sees_only_own_payments(self):
        checkout_order(self.client, self.customer, self.restaurant)
        other_customer = make_customer("other@gmail.com")
        checkout_order(self.client, other_customer, self.restaurant)

        self.client.force_authenticate(user=self.customer)
        response = self.client.get(reverse("payments:my-payment-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

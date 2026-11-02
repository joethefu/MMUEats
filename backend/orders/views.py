from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsCustomer, IsVendor
from common.utils import write_audit_log
from meals.models import Meal
from .models import Cart, CartItem, Order, OrderItem
from .serializers import (
    AddCartItemSerializer,
    CartSerializer,
    CheckoutSerializer,
    OrderSerializer,
    OrderStatusUpdateSerializer,
)


class CartView(APIView):
    """
    Single-endpoint cart management for the logged-in customer (spec §35).
    GET returns the cart; POST adds/updates an item; DELETE clears the cart or
    removes one item via ?item_id=.
    """

    permission_classes = [IsAuthenticated, IsCustomer]

    def get_cart(self, request):
        cart, _ = Cart.objects.get_or_create(customer=request.user)
        return cart

    def get(self, request):
        cart = self.get_cart(request)
        return Response(CartSerializer(cart, context={"request": request}).data)

    def post(self, request):
        serializer = AddCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        meal = serializer.meal
        cart = self.get_cart(request)

        # Enforce single-restaurant cart (spec assumption — standard food-delivery UX).
        if cart.items.exists() and cart.restaurant_id and cart.restaurant_id != meal.restaurant_id:
            return Response(
                {
                    "error": {
                        "code": "different_restaurant",
                        "message": "Your cart has items from another restaurant. Clear it first to order from here.",
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )

        cart.restaurant = meal.restaurant
        cart.save(update_fields=["restaurant"])

        item, created = CartItem.objects.get_or_create(
            cart=cart, meal=meal,
            defaults={
                "quantity": serializer.validated_data["quantity"],
                "special_instructions": serializer.validated_data["special_instructions"],
            },
        )
        if not created:
            item.quantity = serializer.validated_data["quantity"]
            item.special_instructions = serializer.validated_data["special_instructions"] or item.special_instructions
            item.save()

        return Response(CartSerializer(cart, context={"request": request}).data)

    def delete(self, request):
        cart = self.get_cart(request)
        item_id = request.query_params.get("item_id")
        if item_id:
            cart.items.filter(pk=item_id).delete()
            if not cart.items.exists():
                cart.restaurant = None
                cart.save(update_fields=["restaurant"])
        else:
            cart.items.all().delete()
            cart.restaurant = None
            cart.save(update_fields=["restaurant"])
        return Response(CartSerializer(cart, context={"request": request}).data)


class CheckoutView(APIView):
    """Converts the customer's cart into an Order (spec §36-38)."""

    permission_classes = [IsAuthenticated, IsCustomer]

    @transaction.atomic
    def post(self, request):
        cart = Cart.objects.filter(customer=request.user).first()
        if not cart or not cart.items.exists():
            return Response(
                {"error": {"code": "empty_cart", "message": "Your cart is empty."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        restaurant = cart.restaurant
        if not restaurant or not restaurant.is_orderable:
            return Response(
                {"error": {"code": "restaurant_unavailable", "message": "This restaurant isn't accepting orders right now."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        cart_items = list(cart.items.select_related("meal").all())
        for ci in cart_items:
            if not ci.meal.is_available or not ci.meal.is_in_stock:
                return Response(
                    {
                        "error": {
                            "code": "meal_unavailable",
                            "message": f"'{ci.meal.name}' is no longer available. Remove it from your cart to continue.",
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        subtotal = sum((ci.line_total for ci in cart_items), start=0)
        delivery_fee = restaurant.delivery_fee
        discount_amount = 0
        coupon = None

        coupon_code = data.get("coupon_code", "").strip()
        if coupon_code:
            from promotions.services import CouponError, validate_and_price_coupon

            try:
                coupon, discount_amount, free_delivery = validate_and_price_coupon(
                    coupon_code, request.user, restaurant, subtotal, delivery_fee
                )
                if free_delivery:
                    delivery_fee = 0
            except CouponError as exc:
                return Response(
                    {"error": {"code": exc.code, "message": exc.message}},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        total = subtotal + delivery_fee - discount_amount

        order = Order.objects.create(
            customer=request.user,
            restaurant=restaurant,
            delivery_campus_location=data["delivery_campus_location"],
            delivery_directions=data["delivery_directions"],
            payment_method=data["payment_method"],
            special_instructions=data["special_instructions"],
            coupon_code=data["coupon_code"],
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            discount_amount=discount_amount,
            total=total,
            estimated_preparation_minutes=restaurant.average_delivery_minutes,
        )

        for ci in cart_items:
            OrderItem.objects.create(
                order=order,
                meal=ci.meal,
                meal_name=ci.meal.name,
                unit_price=ci.meal.discounted_price,
                packaging_fee=ci.meal.packaging_fee,
                quantity=ci.quantity,
                special_instructions=ci.special_instructions,
            )
            ci.meal.order_count += ci.quantity
            if ci.meal.stock_quantity is not None:
                ci.meal.stock_quantity = max(0, ci.meal.stock_quantity - ci.quantity)
            ci.meal.save(update_fields=["order_count", "stock_quantity"])

        cart.items.all().delete()
        cart.restaurant = None
        cart.save(update_fields=["restaurant"])

        if coupon is not None:
            from promotions.services import redeem_coupon
            redeem_coupon(coupon, request.user, order)

        # Every order gets a Payment record so history/status is uniform across
        # methods — COD starts pending and is marked paid on delivery; M-Pesa
        # starts pending and the frontend immediately triggers the STK push.
        from payments.models import Payment
        Payment.objects.create(order=order, method=order.payment_method, amount=order.total)

        return Response(OrderSerializer(order, context={"request": request}).data, status=status.HTTP_201_CREATED)


def _notify_customer_of_status(order, new_status):
    """Spec §41: order-lifecycle notifications to the customer."""
    from notifications.models import Notification

    mapping = {
        Order.Status.ACCEPTED: (Notification.Type.ORDER_ACCEPTED, "Order accepted!", f"{order.restaurant.name} has accepted your order #{order.order_number}."),
        Order.Status.PREPARING: (Notification.Type.ORDER_PREPARING, "Your food is being prepared", f"{order.restaurant.name} is preparing order #{order.order_number}."),
        Order.Status.READY_FOR_PICKUP: (Notification.Type.ORDER_READY, "Your food is ready", f"Order #{order.order_number} is ready and waiting for a delivery partner."),
        Order.Status.OUT_FOR_DELIVERY: (Notification.Type.ORDER_OUT_FOR_DELIVERY, "Out for delivery", f"Order #{order.order_number} is on its way to you."),
        Order.Status.DELIVERED: (Notification.Type.ORDER_DELIVERED, "Order delivered", f"Order #{order.order_number} has been delivered. Enjoy your meal!"),
        Order.Status.CANCELLED: (Notification.Type.ORDER_CANCELLED, "Order cancelled", f"Order #{order.order_number} was cancelled."),
        Order.Status.REJECTED: (Notification.Type.ORDER_CANCELLED, "Order rejected", f"{order.restaurant.name} was unable to accept order #{order.order_number}."),
    }
    entry = mapping.get(new_status)
    if entry:
        from notifications.services import notify_user
        notif_type, title, message = entry
        notify_user(order.customer, notif_type, title, message, data={"order_id": str(order.id)})


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Role-scoped order visibility:
    - customer sees only their own orders
    - vendor sees only their restaurant's orders
    - admin sees everything
    Status transitions happen through the `update_status` action, not raw PATCH,
    so every transition is validated server-side (spec §39).
    """

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Order.objects.select_related("restaurant", "customer").prefetch_related("items")
        if user.role == "customer":
            return qs.filter(customer=user)
        if user.role == "vendor":
            return qs.filter(restaurant__owner=user)
        if user.role == "delivery_partner":
            return qs.filter(delivery__delivery_partner=user)
        if user.role == "admin":
            return qs
        return qs.none()

    @action(detail=True, methods=["post"])
    def update_status(self, request, pk=None):
        order = self.get_object()

        allowed_for_role = Order.ALLOWED_TRANSITIONS_BY_ROLE.get(request.user.role, set())
        serializer = OrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data["status"]

        if new_status not in allowed_for_role:
            return Response(
                {
                    "error": {
                        "code": "permission_denied",
                        "message": f"Your role cannot set an order to '{new_status}'.",
                    }
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if not order.can_transition_to(new_status):
            return Response(
                {
                    "error": {
                        "code": "invalid_transition",
                        "message": f"Cannot move an order from '{order.status}' to '{new_status}'.",
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = new_status
        now = timezone.now()
        if new_status == Order.Status.ACCEPTED:
            order.accepted_at = now
            if serializer.validated_data.get("estimated_preparation_minutes"):
                order.estimated_preparation_minutes = serializer.validated_data["estimated_preparation_minutes"]
        elif new_status == Order.Status.READY_FOR_PICKUP:
            order.ready_at = now
        elif new_status == Order.Status.DELIVERED:
            order.delivered_at = now
            if order.payment_method == Order.PaymentMethod.CASH_ON_DELIVERY:
                order.payment_status = Order.PaymentStatus.PAID
                from payments.models import Payment
                Payment.objects.filter(order=order).update(status=Payment.Status.PAID)
        elif new_status in (Order.Status.CANCELLED, Order.Status.REJECTED):
            order.cancelled_at = now
            order.cancellation_reason = serializer.validated_data.get("reason", "")
        order.save()

        if new_status == Order.Status.READY_FOR_PICKUP:
            # Spec §38: "Available Delivery Partners notified" — open a pool slot.
            from deliveries.models import Delivery
            Delivery.objects.get_or_create(order=order)

        if new_status in (Order.Status.PICKED_UP, Order.Status.OUT_FOR_DELIVERY, Order.Status.DELIVERED):
            from deliveries.models import Delivery
            try:
                delivery = order.delivery
            except Delivery.DoesNotExist:
                delivery = None
            if delivery and delivery.delivery_partner_id == request.user.id:
                if new_status == Order.Status.PICKED_UP:
                    delivery.picked_up_at = now
                elif new_status == Order.Status.OUT_FOR_DELIVERY:
                    delivery.out_for_delivery_at = now
                elif new_status == Order.Status.DELIVERED:
                    delivery.delivered_at = now
                    delivery.earnings = order.delivery_fee
                    from deliveries.models import DeliveryPartnerProfile
                    profile, _ = DeliveryPartnerProfile.objects.get_or_create(user=request.user)
                    profile.total_deliveries += 1
                    profile.total_earnings += order.delivery_fee
                    profile.save(update_fields=["total_deliveries", "total_earnings"])
                delivery.save()

        write_audit_log(request.user, f"order_status_{new_status}", obj=order, request=request)

        from notifications.services import broadcast_order_update
        broadcast_order_update(order)
        _notify_customer_of_status(order, new_status)

        return Response(OrderSerializer(order, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Spec §21: customer can cancel before preparation begins."""
        order = self.get_object()
        if order.customer_id != request.user.id and request.user.role != "admin":
            return Response({"error": {"code": "permission_denied", "message": "Not your order."}}, status=403)

        if not order.can_be_cancelled_by_customer:
            return Response(
                {"error": {"code": "too_late", "message": "This order can no longer be cancelled."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = Order.Status.CANCELLED
        order.cancelled_at = timezone.now()
        order.cancellation_reason = request.data.get("reason", "Cancelled by customer")
        order.save()
        write_audit_log(request.user, "order_cancelled_by_customer", obj=order, request=request)
        return Response(OrderSerializer(order, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def reorder(self, request, pk=None):
        """Spec §21: reorder previous meals — rebuilds the customer's cart from this order."""
        order = self.get_object()
        if order.customer_id != request.user.id:
            return Response({"error": {"code": "permission_denied", "message": "Not your order."}}, status=403)

        cart, _ = Cart.objects.get_or_create(customer=request.user)
        cart.items.all().delete()
        cart.restaurant = order.restaurant
        cart.save(update_fields=["restaurant"])

        skipped = []
        for oi in order.items.select_related("meal").all():
            if oi.meal is None or not oi.meal.is_available or not oi.meal.is_in_stock:
                skipped.append(oi.meal_name)
                continue
            CartItem.objects.create(cart=cart, meal=oi.meal, quantity=oi.quantity, special_instructions=oi.special_instructions)

        response_data = CartSerializer(cart, context={"request": request}).data
        if skipped:
            response_data["skipped_unavailable"] = skipped
        return Response(response_data)

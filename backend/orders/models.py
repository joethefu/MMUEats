import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from common.models import TimeStampedModel
from meals.models import Meal
from restaurants.models import Restaurant


class Cart(TimeStampedModel):
    """
    One active cart per customer. Deliberately restricted to a single restaurant
    at a time (industry-standard pattern) — adding a meal from a different
    restaurant prompts the customer to clear the cart first (enforced in the view).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart")
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    coupon_code = models.CharField(max_length=40, blank=True)

    def __str__(self):
        return f"Cart({self.customer.email})"


class CartItem(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name="+")
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    special_instructions = models.CharField(max_length=255, blank=True)  # e.g. "No onions"

    class Meta:
        unique_together = ("cart", "meal")

    def __str__(self):
        return f"{self.quantity}x {self.meal.name}"

    @property
    def line_total(self):
        return (self.meal.discounted_price + self.meal.packaging_fee) * self.quantity

    @property
    def packaging_total(self):
        return self.meal.packaging_fee * self.quantity


class Order(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        PREPARING = "preparing", "Preparing"
        READY_FOR_PICKUP = "ready_for_pickup", "Ready for Pickup"
        PICKED_UP = "picked_up", "Picked Up"
        OUT_FOR_DELIVERY = "out_for_delivery", "Out for Delivery"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"
        REJECTED = "rejected", "Rejected"

    # Statuses reachable from each status — enforced server-side (spec §39).
    ALLOWED_TRANSITIONS = {
        Status.PENDING: {Status.ACCEPTED, Status.REJECTED, Status.CANCELLED},
        Status.ACCEPTED: {Status.PREPARING, Status.CANCELLED},
        Status.PREPARING: {Status.READY_FOR_PICKUP, Status.CANCELLED},
        Status.READY_FOR_PICKUP: {Status.PICKED_UP},
        Status.PICKED_UP: {Status.OUT_FOR_DELIVERY},
        Status.OUT_FOR_DELIVERY: {Status.DELIVERED},
        Status.DELIVERED: set(),
        Status.CANCELLED: set(),
        Status.REJECTED: set(),
    }

    ALLOWED_TRANSITIONS_BY_ROLE = {
        "vendor": {Status.ACCEPTED, Status.PREPARING, Status.READY_FOR_PICKUP, Status.REJECTED, Status.CANCELLED},
        "delivery_partner": {Status.PICKED_UP, Status.OUT_FOR_DELIVERY, Status.DELIVERED},
        "admin": set(Status.values),
    }

    class PaymentMethod(models.TextChoices):
        MPESA = "mpesa", "M-Pesa"
        CASH_ON_DELIVERY = "cash_on_delivery", "Cash on Delivery"
        WALLET = "wallet", "Student Wallet"  # future

    class PaymentStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=20, unique=True, editable=False)

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders")
    restaurant = models.ForeignKey(Restaurant, on_delete=models.PROTECT, related_name="orders")

    delivery_campus_location = models.CharField(max_length=100)
    delivery_directions = models.CharField(max_length=255, blank=True)

    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.CASH_ON_DELIVERY)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    coupon_code = models.CharField(max_length=40, blank=True)
    special_instructions = models.CharField(max_length=255, blank=True)

    estimated_preparation_minutes = models.PositiveIntegerField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    ready_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["customer", "-created_at"]),
            models.Index(fields=["restaurant", "status"]),
            models.Index(fields=["status"]),
        ]

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"MMU{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.order_number} ({self.status})"

    def can_transition_to(self, new_status):
        return new_status in self.ALLOWED_TRANSITIONS.get(self.status, set())

    @property
    def can_be_cancelled_by_customer(self):
        # Spec §21: "Cancel order before preparation"
        return self.status == self.Status.PENDING or self.status == self.Status.ACCEPTED


class OrderItem(TimeStampedModel):
    """Snapshotted at order time so later menu edits don't rewrite order history."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    meal = models.ForeignKey(Meal, on_delete=models.SET_NULL, null=True, related_name="+")

    meal_name = models.CharField(max_length=150)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    packaging_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0)  # per unit, snapshot
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    special_instructions = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.quantity}x {self.meal_name}"

    @property
    def line_total(self):
        return (self.unit_price + self.packaging_fee) * self.quantity

import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from common.models import TimeStampedModel
from restaurants.models import Restaurant


class Coupon(TimeStampedModel):
    """Spec §50: coupons/promo codes. Admin-controlled; optionally scoped to one restaurant."""

    class DiscountType(models.TextChoices):
        PERCENTAGE = "percentage", "Percentage"
        FIXED_AMOUNT = "fixed_amount", "Fixed Amount"
        FREE_DELIVERY = "free_delivery", "Free Delivery"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=30, unique=True)
    description = models.CharField(max_length=255, blank=True)
    discount_type = models.CharField(max_length=20, choices=DiscountType.choices, default=DiscountType.PERCENTAGE)
    discount_value = models.DecimalField(max_digits=8, decimal_places=2, default=0)  # % (0-100) or KES amount
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_discount_amount = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)  # cap for percentage type

    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.CASCADE, null=True, blank=True, related_name="coupons"
    )  # null = platform-wide

    max_uses = models.PositiveIntegerField(null=True, blank=True)  # null = unlimited
    max_uses_per_customer = models.PositiveIntegerField(default=1)
    used_count = models.PositiveIntegerField(default=0)

    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["code"]), models.Index(fields=["is_active"])]

    def __str__(self):
        return self.code

    @property
    def is_currently_valid(self):
        now = timezone.now()
        if not self.is_active or not (self.valid_from <= now <= self.valid_until):
            return False
        if self.max_uses is not None and self.used_count >= self.max_uses:
            return False
        return True

    def compute_discount(self, subtotal, delivery_fee):
        """Returns (discount_amount, free_delivery: bool) for the given order totals."""
        if self.discount_type == self.DiscountType.FREE_DELIVERY:
            return Decimal("0.00"), True
        if self.discount_type == self.DiscountType.FIXED_AMOUNT:
            return min(self.discount_value, subtotal), False
        # percentage
        amount = (subtotal * self.discount_value / Decimal(100)).quantize(Decimal("0.01"))
        if self.max_discount_amount is not None:
            amount = min(amount, self.max_discount_amount)
        return min(amount, subtotal), False


class CouponRedemption(TimeStampedModel):
    """Tracks per-customer usage so max_uses_per_customer can be enforced."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name="redemptions")
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="coupon_redemptions")
    order = models.OneToOneField("orders.Order", on_delete=models.CASCADE, related_name="coupon_redemption")

    class Meta:
        indexes = [models.Index(fields=["coupon", "customer"])]

    def __str__(self):
        return f"{self.coupon.code} used by {self.customer.email}"

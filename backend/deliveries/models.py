import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from common.models import TimeStampedModel
from orders.models import Order


class DeliveryPartnerProfile(TimeStampedModel):
    """
    Extends a User(role=delivery_partner) with delivery-specific state.
    Spec §26-27: online/offline toggle, earnings, delivery history stats.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="delivery_partner_profile")
    is_online = models.BooleanField(default=False)
    vehicle_type = models.CharField(max_length=50, blank=True)  # bicycle, motorbike, on foot

    total_deliveries = models.PositiveIntegerField(default=0)
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    ratings_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"DeliveryPartnerProfile({self.user.email})"


class Delivery(TimeStampedModel):
    """
    One per Order. Created automatically the moment a vendor marks an order
    'ready_for_pickup' (spec §38: "Available Delivery Partners notified").
    Sits in an unassigned pool (delivery_partner=None) until a partner accepts it.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="delivery")
    delivery_partner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="deliveries"
    )

    accepted_at = models.DateTimeField(null=True, blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    out_for_delivery_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    earnings = models.DecimalField(max_digits=8, decimal_places=2, default=0)  # set on completion = order.delivery_fee
    distance_km = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["delivery_partner"])]

    def __str__(self):
        return f"Delivery for {self.order.order_number}"

    @property
    def is_available(self):
        return self.delivery_partner_id is None and self.order.status == Order.Status.READY_FOR_PICKUP


class DeliveryPartnerReview(TimeStampedModel):
    """Spec §51: customers rate delivery partners (speed) separately from the restaurant."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    delivery = models.OneToOneField(Delivery, on_delete=models.CASCADE, related_name="review")
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="delivery_reviews")
    delivery_partner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_reviews")
    speed_rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)

    def __str__(self):
        return f"{self.speed_rating}★ for {self.delivery_partner.email}"

import uuid

from django.conf import settings
from django.db import models

from common.models import TimeStampedModel


class Notification(TimeStampedModel):
    """
    Spec §41: in-app notification record backing the customer/vendor/delivery/
    admin "Notifications" pages, plus the source-of-truth for what gets pushed
    via FCM/email. One row per event per recipient.
    """

    class Type(models.TextChoices):
        ACCOUNT_VERIFICATION = "account_verification", "Account Verification"
        PASSWORD_RESET = "password_reset", "Password Reset"
        ORDER_ACCEPTED = "order_accepted", "Order Accepted"
        ORDER_PREPARING = "order_preparing", "Food Preparing"
        ORDER_READY = "order_ready", "Food Ready"
        DELIVERY_PARTNER_ASSIGNED = "delivery_partner_assigned", "Delivery Partner Assigned"
        ORDER_OUT_FOR_DELIVERY = "order_out_for_delivery", "Out for Delivery"
        ORDER_DELIVERED = "order_delivered", "Order Delivered"
        ORDER_CANCELLED = "order_cancelled", "Order Cancelled"
        NEW_ORDER = "new_order", "New Order Received"  # for vendors
        NEW_DELIVERY_AVAILABLE = "new_delivery_available", "New Delivery Available"  # for partners
        VENDOR_APPLICATION_STATUS = "vendor_application_status", "Vendor Application Status"
        DELIVERY_APPLICATION_STATUS = "delivery_application_status", "Delivery Application Status"
        PROMOTION = "promotion", "Promotion Alert"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    notification_type = models.CharField(max_length=40, choices=Type.choices, default=Type.OTHER)
    title = models.CharField(max_length=150)
    message = models.CharField(max_length=500)
    data = models.JSONField(default=dict, blank=True)  # e.g. {"order_id": "..."} for client-side deep-linking

    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"{self.notification_type} -> {self.user.email}"


class DeviceToken(TimeStampedModel):
    """FCM registration token for push notifications (spec §41). One user can have several (web + mobile)."""

    class Platform(models.TextChoices):
        WEB = "web", "Web"
        ANDROID = "android", "Android"
        IOS = "ios", "iOS"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="device_tokens")
    token = models.CharField(max_length=255, unique=True)
    platform = models.CharField(max_length=10, choices=Platform.choices, default=Platform.WEB)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.platform} token for {self.user.email}"

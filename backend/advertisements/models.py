import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from common.models import TimeStampedModel


class Advertisement(TimeStampedModel):
    """Spec §42-46: admin-managed advertisements shown as a startup popup, homepage
    banner, or promotional section, within a scheduled date range."""

    class Placement(models.TextChoices):
        STARTUP_POPUP = "startup_popup", "Startup Popup"
        HOMEPAGE_BANNER = "homepage_banner", "Homepage Banner"
        PROMOTIONAL_SECTION = "promotional_section", "Promotional Section"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=150)
    image = models.ImageField(upload_to="advertisements/")
    description = models.CharField(max_length=255, blank=True)
    cta_label = models.CharField(max_length=40, blank=True)  # optional button text
    # Internal path ("/restaurants/my-vendor"), or full external URL ("https://...").
    external_url = models.CharField(max_length=500, blank=True)
    placement = models.CharField(max_length=30, choices=Placement.choices, default=Placement.STARTUP_POPUP)

    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    priority = models.PositiveIntegerField(default=0)  # higher = shown first when several are active

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_advertisements"
    )

    class Meta:
        ordering = ["-priority", "-created_at"]
        indexes = [
            models.Index(fields=["placement", "is_active"]),
            models.Index(fields=["start_date", "end_date"]),
        ]

    def __str__(self):
        return self.title

    @property
    def is_currently_valid(self):
        today = timezone.localdate()
        return self.is_active and self.start_date <= today <= self.end_date


class AdvertisementImpression(TimeStampedModel):
    """
    Spec §46-47: view-count tracking. Anonymous viewers are tracked only by an
    opaque client-generated device_id (never IP/user-agent), keeping personal
    data collection to a minimum.
    """

    class Platform(models.TextChoices):
        WEB = "web", "Web"
        ANDROID = "android", "Android"
        IOS = "ios", "iOS"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    advertisement = models.ForeignKey(Advertisement, on_delete=models.CASCADE, related_name="impressions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    device_id = models.CharField(max_length=100, blank=True)
    platform = models.CharField(max_length=10, choices=Platform.choices, default=Platform.WEB)

    class Meta:
        indexes = [models.Index(fields=["advertisement", "created_at"])]


class AdvertisementClick(TimeStampedModel):
    class Platform(models.TextChoices):
        WEB = "web", "Web"
        ANDROID = "android", "Android"
        IOS = "ios", "iOS"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    advertisement = models.ForeignKey(Advertisement, on_delete=models.CASCADE, related_name="clicks")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    device_id = models.CharField(max_length=100, blank=True)
    destination_url = models.CharField(max_length=500, blank=True)
    platform = models.CharField(max_length=10, choices=Platform.choices, default=Platform.WEB)

    class Meta:
        indexes = [models.Index(fields=["advertisement", "created_at"])]

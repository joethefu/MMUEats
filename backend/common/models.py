import uuid

from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base adding created_at / updated_at to every model that needs them."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AuditLog(models.Model):
    """
    Records important administrative actions across the platform.
    Populated explicitly by views/services that perform sensitive actions
    (vendor approval, suspensions, advertisement changes, etc.) — see
    common.utils.write_audit_log().
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=100)
    object_type = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=100, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["action"]),
            models.Index(fields=["object_type", "object_id"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"{self.action} by {self.actor_id} at {self.created_at}"

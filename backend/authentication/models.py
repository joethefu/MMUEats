import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from common.utils import generate_secure_token


class BaseToken(models.Model):
    """Shared behavior for one-time, expiring security tokens."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.CharField(max_length=64, unique=True, db_index=True, default=generate_secure_token)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    @property
    def is_used(self):
        return self.used_at is not None

    @property
    def is_valid(self):
        return not self.is_expired and not self.is_used

    def mark_used(self):
        self.used_at = timezone.now()
        self.save(update_fields=["used_at"])


class EmailVerificationToken(BaseToken):
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(
                hours=settings.EMAIL_VERIFICATION_TOKEN_LIFETIME_HOURS
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"EmailVerificationToken(user={self.user_id}, used={self.is_used})"


class PasswordResetToken(BaseToken):
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(
                hours=settings.PASSWORD_RESET_TOKEN_LIFETIME_HOURS
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"PasswordResetToken(user={self.user_id}, used={self.is_used})"

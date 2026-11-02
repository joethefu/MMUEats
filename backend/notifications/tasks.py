import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger("django")


@shared_task(bind=True, max_retries=2, default_retry_delay=20)
def send_notification_email(self, user_email, subject, message):
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user_email], fail_silently=False)
    except Exception as exc:
        logger.warning("Failed to send notification email to %s: %s", user_email, exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=20)
def send_push_to_user(self, user_id, title, body, data=None):
    """Fans a push out to every active device token registered for a user."""
    from . import fcm_service
    from .models import DeviceToken

    tokens = DeviceToken.objects.filter(user_id=user_id, is_active=True)
    for device in tokens:
        still_valid = fcm_service.send_push(device.token, title, body, data)
        if not still_valid:
            device.is_active = False
            device.save(update_fields=["is_active"])

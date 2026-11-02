"""
Firebase Cloud Messaging integration.

DEVELOPMENT MODE: when FIREBASE_CONFIG is not set, push sends are logged
instead of actually dispatched, so development never blocks on Firebase
project setup. Set FIREBASE_CONFIG (the service account JSON, as a string)
in .env to enable real pushes — no other code needs to change.
"""

import json
import logging

from django.conf import settings

logger = logging.getLogger("django")

_firebase_app = None


def _is_configured():
    return bool(settings.FIREBASE_CONFIG)


def _get_app():
    """Lazily initializes the Firebase Admin SDK app, once, from FIREBASE_CONFIG."""
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app

    import firebase_admin
    from firebase_admin import credentials

    cred_dict = json.loads(settings.FIREBASE_CONFIG)
    cred = credentials.Certificate(cred_dict)
    _firebase_app = firebase_admin.initialize_app(cred)
    return _firebase_app


def send_push(token, title, body, data=None):
    """
    Sends a single push notification. Returns True on (attempted) success,
    False if the token should be deactivated (e.g. unregistered/invalid).
    """
    if not _is_configured():
        logger.info("[MOCK FCM] Would push to token=%s...: '%s' — %s", token[:12], title, body)
        return True

    from firebase_admin import messaging

    _get_app()
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        data={k: str(v) for k, v in (data or {}).items()},
        token=token,
    )
    try:
        messaging.send(message)
        return True
    except messaging.UnregisteredError:
        logger.info("FCM token no longer valid, deactivating: %s...", token[:12])
        return False
    except Exception as exc:
        logger.warning("FCM push failed for token %s...: %s", token[:12], exc)
        return True  # transient failure — keep the token, don't deactivate

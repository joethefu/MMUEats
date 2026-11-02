"""
Central fan-out point for every notification in the system. Call notify_user()
from anywhere an event happens (order status change, delivery assignment,
partner approval, etc.) — it handles the in-app record, the live WebSocket
push to anyone currently connected, and (optionally) email/FCM push.
"""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Notification
from .tasks import send_notification_email, send_push_to_user


def notify_user(user, notification_type, title, message, data=None, send_email=False):
    notification = Notification.objects.create(
        user=user, notification_type=notification_type, title=title, message=message, data=data or {}
    )

    _broadcast_to_user(user.id, {
        "event": "notification",
        "id": str(notification.id),
        "notification_type": notification_type,
        "title": title,
        "message": message,
        "data": data or {},
        "created_at": notification.created_at.isoformat(),
    })

    send_push_to_user.delay(str(user.id), title, message, data or {})

    if send_email and user.email:
        send_notification_email.delay(user.email, title, message)

    return notification


def broadcast_order_update(order):
    """Live-pushes an order's new status to its customer (and anyone else watching), independent of notify_user."""
    payload = {
        "event": "order_update",
        "order_id": str(order.id),
        "order_number": order.order_number,
        "status": order.status,
    }
    _broadcast_to_user(order.customer_id, payload)


def _broadcast_to_user(user_id, payload):
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    try:
        async_to_sync(channel_layer.group_send)(
            f"user_{user_id}",
            {"type": "notification.message", "payload": payload},
        )
    except Exception:
        # Real-time push is a nice-to-have — never let a channel-layer hiccup
        # break the underlying business operation (order update, etc.).
        pass

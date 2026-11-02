import json

from channels.generic.websocket import AsyncJsonWebsocketConsumer


class UserNotificationConsumer(AsyncJsonWebsocketConsumer):
    """
    One socket per logged-in user: ws://.../ws/notifications/
    Authenticated via JWT passed as a query param (?token=...), decoded in
    notifications.middleware.JWTAuthMiddleware before the connection reaches here.
    Receives: new in-app notifications, live order status updates for any order
    the user is a party to (pushed from orders.views via group_send).
    """

    async def connect(self):
        user = self.scope.get("user")
        if user is None or not user.is_authenticated:
            await self.close(code=4001)
            return
        self.group_name = f"user_{user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # Called by channel_layer.group_send(..., {"type": "notification.message", ...})
    async def notification_message(self, event):
        await self.send_json(event["payload"])

    async def order_update(self, event):
        await self.send_json(event["payload"])

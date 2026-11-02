from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import DeviceToken, Notification
from .serializers import DeviceTokenSerializer, NotificationSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return Response({"unread_count": count})

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=["is_read", "read_at"])
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        now = timezone.now()
        self.get_queryset().filter(is_read=False).update(is_read=True, read_at=now)
        return Response({"success": True})


class DeviceTokenViewSet(viewsets.ModelViewSet):
    serializer_class = DeviceTokenSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "delete"]

    def get_queryset(self):
        return DeviceToken.objects.filter(user=self.request.user)

from django.contrib import admin

from .models import DeviceToken, Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "notification_type", "title", "is_read", "created_at")
    list_filter = ("notification_type", "is_read")
    search_fields = ("user__email", "title")


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "platform", "is_active", "created_at")
    list_filter = ("platform", "is_active")

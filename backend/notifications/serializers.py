from rest_framework import serializers

from .models import DeviceToken, Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "notification_type", "title", "message", "data", "is_read", "read_at", "created_at"]
        read_only_fields = fields


class DeviceTokenSerializer(serializers.ModelSerializer):
    # Uniqueness is handled explicitly via update_or_create in create() below —
    # a re-registered token reassigning to a new user is expected, not an error,
    # so the model field's auto-generated UniqueValidator must be disabled here.
    token = serializers.CharField(max_length=255, validators=[])

    class Meta:
        model = DeviceToken
        fields = ["id", "token", "platform", "is_active", "created_at"]
        read_only_fields = ["id", "is_active", "created_at"]

    def create(self, validated_data):
        user = self.context["request"].user
        obj, _ = DeviceToken.objects.update_or_create(
            token=validated_data["token"],
            defaults={"user": user, "platform": validated_data.get("platform", "web"), "is_active": True},
        )
        return obj

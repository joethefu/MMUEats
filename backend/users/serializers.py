from rest_framework import serializers

from .models import DeliveryLocation, DeliveryPartnerApplication, User, VendorApplication


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "full_name", "email", "phone_number", "role",
            "is_email_verified", "is_approved", "profile_picture", "created_at",
        ]
        read_only_fields = ["id", "email", "role", "is_email_verified", "is_approved", "created_at"]

    MAX_PICTURE_BYTES = 5 * 1024 * 1024

    def validate_profile_picture(self, value):
        if value is None:
            return value
        if value.size > self.MAX_PICTURE_BYTES:
            raise serializers.ValidationError("Image is too large. Maximum size is 5 MB.")
        content_type = getattr(value, "content_type", "") or ""
        if content_type and not content_type.startswith("image/"):
            raise serializers.ValidationError("Upload a valid image file (JPG, PNG or WebP).")
        return value


class DeliveryLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryLocation
        fields = ["id", "label", "campus_location", "additional_directions", "is_default", "created_at"]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        user = self.context["request"].user
        if validated_data.get("is_default"):
            DeliveryLocation.objects.filter(user=user, is_default=True).update(is_default=False)
        return DeliveryLocation.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        if validated_data.get("is_default"):
            DeliveryLocation.objects.filter(user=instance.user, is_default=True).exclude(pk=instance.pk).update(
                is_default=False
            )
        return super().update(instance, validated_data)


class VendorApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorApplication
        fields = [
            "id", "business_name", "owner_name", "email", "phone_number",
            "business_location", "food_categories", "description", "logo",
            "status", "review_notes", "created_at",
        ]
        read_only_fields = ["id", "status", "review_notes", "created_at"]


class DeliveryPartnerApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryPartnerApplication
        fields = [
            "id", "full_name", "email", "phone_number", "preferred_area",
            "availability", "profile_picture", "status", "review_notes", "created_at",
        ]
        read_only_fields = ["id", "status", "review_notes", "created_at"]


class ApplicationReviewSerializer(serializers.Serializer):
    ACTION_CHOICES = ("approve", "reject", "needs_info")
    action = serializers.ChoiceField(choices=ACTION_CHOICES)
    notes = serializers.CharField(required=False, allow_blank=True, default="")

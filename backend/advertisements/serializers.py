from rest_framework import serializers
from rest_framework.fields import empty

from .models import Advertisement, AdvertisementClick, AdvertisementImpression


class ExplicitBooleanField(serializers.BooleanField):
    """
    DRF's BooleanField treats a missing key in multipart/form-data as an HTML
    checkbox convention — "absent means unchecked (False)" — which silently
    overrides the model's `default=True` for is_active whenever a client
    (e.g. a multipart create that only sends the image + text fields) omits
    the field. That's the wrong semantics for a REST API: omitting a field
    should mean "use the default," not "explicitly set to False." This
    subclass restores normal REST/JSON semantics for both multipart and JSON
    requests.
    """

    def get_value(self, dictionary):
        if self.field_name not in dictionary:
            return empty
        return super().get_value(dictionary)


class AdvertisementPublicSerializer(serializers.ModelSerializer):
    """What the storefront actually needs to render + track an ad — no admin-only fields."""

    class Meta:
        model = Advertisement
        fields = ["id", "title", "description", "cta_label", "image", "external_url", "placement"]
        read_only_fields = fields


class AdvertisementAdminSerializer(serializers.ModelSerializer):
    impressions_count = serializers.IntegerField(source="impressions.count", read_only=True)
    clicks_count = serializers.IntegerField(source="clicks.count", read_only=True)
    is_active = ExplicitBooleanField(required=False, default=True)

    class Meta:
        model = Advertisement
        fields = [
            "id", "title", "description", "cta_label", "image", "external_url", "placement",
            "start_date", "end_date", "is_active", "priority",
            "is_currently_valid", "impressions_count", "clicks_count",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "is_currently_valid", "impressions_count", "clicks_count", "created_at", "updated_at"]

    def validate_external_url(self, value):
        value = (value or "").strip()
        if value and not (value.startswith("/") and not value.startswith("//")) and not value.startswith(("http://", "https://")):
            raise serializers.ValidationError("Use an internal path like /restaurants or a full http(s) URL.")
        return value

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class TrackingEventSerializer(serializers.Serializer):
    """Shared shape for both impression and click tracking calls."""

    device_id = serializers.CharField(required=False, allow_blank=True, default="")
    platform = serializers.ChoiceField(choices=AdvertisementImpression.Platform.choices, default="web")

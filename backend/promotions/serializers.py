from rest_framework import serializers

from .models import Coupon


class CouponAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = [
            "id", "code", "description", "discount_type", "discount_value",
            "min_order_amount", "max_discount_amount", "restaurant",
            "max_uses", "max_uses_per_customer", "used_count",
            "valid_from", "valid_until", "is_active", "is_currently_valid", "created_at",
        ]
        read_only_fields = ["id", "used_count", "is_currently_valid", "created_at"]

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        validated_data["code"] = validated_data["code"].strip().upper()
        return super().create(validated_data)

    def validate_code(self, value):
        return value.strip().upper()


class CouponValidateSerializer(serializers.Serializer):
    code = serializers.CharField()
    restaurant_id = serializers.UUIDField()
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = serializers.DecimalField(max_digits=8, decimal_places=2)

from rest_framework import serializers

from .models import Delivery, DeliveryPartnerProfile, DeliveryPartnerReview


class DeliveryPartnerProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = DeliveryPartnerProfile
        fields = [
            "id", "full_name", "is_online", "vehicle_type",
            "total_deliveries", "total_earnings", "average_rating", "ratings_count",
        ]
        read_only_fields = ["id", "full_name", "total_deliveries", "total_earnings", "average_rating", "ratings_count"]


class DeliverySerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source="order.order_number", read_only=True)
    restaurant_name = serializers.CharField(source="order.restaurant.name", read_only=True)
    restaurant_location = serializers.CharField(source="order.restaurant.location", read_only=True)
    delivery_campus_location = serializers.CharField(source="order.delivery_campus_location", read_only=True)
    delivery_directions = serializers.CharField(source="order.delivery_directions", read_only=True)
    customer_name = serializers.CharField(source="order.customer.full_name", read_only=True)
    customer_phone = serializers.CharField(source="order.customer.phone_number", read_only=True)
    order_status = serializers.CharField(source="order.status", read_only=True)
    order_total = serializers.DecimalField(source="order.total", max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Delivery
        fields = [
            "id", "order", "order_number", "order_status", "order_total",
            "restaurant_name", "restaurant_location",
            "delivery_campus_location", "delivery_directions",
            "customer_name", "customer_phone",
            "accepted_at", "picked_up_at", "out_for_delivery_at", "delivered_at",
            "earnings", "created_at",
        ]
        read_only_fields = fields


class DeliveryPartnerReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryPartnerReview
        fields = ["id", "delivery", "speed_rating", "comment", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_delivery(self, delivery):
        request = self.context["request"]
        if delivery.order.customer_id != request.user.id:
            raise serializers.ValidationError("You can only review your own deliveries.")
        if delivery.delivered_at is None:
            raise serializers.ValidationError("You can only review a completed delivery.")
        return delivery

    def create(self, validated_data):
        delivery = validated_data["delivery"]
        validated_data["customer"] = self.context["request"].user
        validated_data["delivery_partner"] = delivery.delivery_partner
        return super().create(validated_data)

from rest_framework import serializers

from meals.models import Meal
from .models import Cart, CartItem, Order, OrderItem


class CartItemSerializer(serializers.ModelSerializer):
    meal_name = serializers.CharField(source="meal.name", read_only=True)
    meal_image = serializers.ImageField(source="meal.image", read_only=True)
    unit_price = serializers.DecimalField(source="meal.discounted_price", max_digits=8, decimal_places=2, read_only=True)
    packaging_fee = serializers.DecimalField(source="meal.packaging_fee", max_digits=6, decimal_places=2, read_only=True)
    line_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ["id", "meal", "meal_name", "meal_image", "unit_price", "packaging_fee", "quantity", "special_instructions", "line_total"]
        read_only_fields = ["id"]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    restaurant_name = serializers.CharField(source="restaurant.name", read_only=True, default=None)
    subtotal = serializers.SerializerMethodField()
    packaging_total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "restaurant", "restaurant_name", "coupon_code", "items", "packaging_total", "subtotal"]

    def get_packaging_total(self, obj):
        return sum((item.packaging_total for item in obj.items.all()), start=0)

    def get_subtotal(self, obj):
        return sum((item.line_total for item in obj.items.all()), start=0)


class AddCartItemSerializer(serializers.Serializer):
    meal_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, default=1)
    special_instructions = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_meal_id(self, value):
        try:
            meal = Meal.objects.select_related("restaurant").get(pk=value)
        except Meal.DoesNotExist:
            raise serializers.ValidationError("This meal no longer exists.")
        if not meal.is_available or not meal.restaurant.is_orderable:
            raise serializers.ValidationError("This meal isn't available right now.")
        if not meal.is_in_stock:
            raise serializers.ValidationError("This meal is currently out of stock.")
        self._meal = meal
        return value

    @property
    def meal(self):
        return self._meal


class OrderItemSerializer(serializers.ModelSerializer):
    line_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "meal", "meal_name", "unit_price", "packaging_fee", "quantity", "special_instructions", "line_total"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    restaurant_name = serializers.CharField(source="restaurant.name", read_only=True)
    restaurant_logo = serializers.ImageField(source="restaurant.logo", read_only=True)
    customer_name = serializers.CharField(source="customer.full_name", read_only=True)
    customer_phone = serializers.CharField(source="customer.phone_number", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "order_number", "restaurant", "restaurant_name", "restaurant_logo",
            "customer_name", "customer_phone",
            "delivery_campus_location", "delivery_directions",
            "status", "payment_method", "payment_status",
            "subtotal", "delivery_fee", "discount_amount", "total",
            "coupon_code", "special_instructions",
            "estimated_preparation_minutes", "accepted_at", "ready_at", "delivered_at",
            "cancelled_at", "cancellation_reason", "can_be_cancelled_by_customer",
            "items", "created_at",
        ]
        read_only_fields = [f for f in fields if f not in ("special_instructions",)]

    can_be_cancelled_by_customer = serializers.BooleanField(read_only=True)


class CheckoutSerializer(serializers.Serializer):
    delivery_campus_location = serializers.CharField()
    delivery_directions = serializers.CharField(required=False, allow_blank=True, default="")
    payment_method = serializers.ChoiceField(choices=Order.PaymentMethod.choices)
    special_instructions = serializers.CharField(required=False, allow_blank=True, default="")
    coupon_code = serializers.CharField(required=False, allow_blank=True, default="")


class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.Status.choices)
    reason = serializers.CharField(required=False, allow_blank=True, default="")
    estimated_preparation_minutes = serializers.IntegerField(required=False, min_value=1)

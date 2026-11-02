from django.utils.text import slugify
from rest_framework import serializers

from .models import FavoriteRestaurant, Restaurant, RestaurantImage, RestaurantReview


class RestaurantListSerializer(serializers.ModelSerializer):
    """Lightweight — used for restaurant listing cards (spec §33)."""

    is_favorited = serializers.SerializerMethodField()
    favorite_id = serializers.SerializerMethodField()

    class Meta:
        model = Restaurant
        fields = [
            "id", "name", "slug", "logo", "location", "status", "is_orderable",
            "average_rating", "ratings_count", "delivery_fee", "average_delivery_minutes",
            "is_favorited", "favorite_id",
        ]

    def _favorite(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        return obj.favorited_by.filter(user=request.user).first()

    def get_is_favorited(self, obj):
        return self._favorite(obj) is not None

    def get_favorite_id(self, obj):
        fav = self._favorite(obj)
        return str(fav.id) if fav else None


class RestaurantDetailSerializer(RestaurantListSerializer):
    class Meta(RestaurantListSerializer.Meta):
        fields = RestaurantListSerializer.Meta.fields + [
            "description", "banner", "phone_number", "email",
            "opening_time", "closing_time", "created_at",
        ]


class RestaurantWriteSerializer(serializers.ModelSerializer):
    """Used by the owning vendor to create/update their storefront (spec §23)."""

    class Meta:
        model = Restaurant
        fields = [
            "name", "description", "logo", "banner", "phone_number", "email",
            "location", "opening_time", "closing_time", "status",
            "delivery_fee", "average_delivery_minutes",
        ]

    def validate(self, attrs):
        request = self.context["request"]
        if self.instance is None and Restaurant.objects.filter(owner=request.user).exists():
            raise serializers.ValidationError("You already have a restaurant profile — edit it instead.")
        return attrs

    def create(self, validated_data):
        owner = self.context["request"].user
        base_slug = slugify(validated_data["name"])
        slug = base_slug
        i = 1
        while Restaurant.objects.filter(slug=slug).exists():
            i += 1
            slug = f"{base_slug}-{i}"
        return Restaurant.objects.create(owner=owner, slug=slug, **validated_data)


class RestaurantImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestaurantImage
        fields = ["id", "image", "caption"]


class FavoriteRestaurantSerializer(serializers.ModelSerializer):
    restaurant_detail = RestaurantListSerializer(source="restaurant", read_only=True)

    class Meta:
        model = FavoriteRestaurant
        fields = ["id", "restaurant", "restaurant_detail", "created_at"]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        user = self.context["request"].user
        obj, _ = FavoriteRestaurant.objects.get_or_create(user=user, restaurant=validated_data["restaurant"])
        return obj


class RestaurantReviewSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.full_name", read_only=True)
    customer_picture = serializers.ImageField(source="customer.profile_picture", read_only=True)

    class Meta:
        model = RestaurantReview
        fields = ["id", "restaurant", "order", "customer", "customer_name", "customer_picture", "rating", "food_quality_rating", "comment", "created_at"]
        read_only_fields = ["id", "customer", "created_at", "customer_name", "customer_picture"]

    def validate_order(self, order):
        request = self.context["request"]
        if order is None:
            return order
        if order.customer_id != request.user.id:
            raise serializers.ValidationError("You can only review your own orders.")
        if order.status != order.Status.DELIVERED:
            raise serializers.ValidationError("You can only review orders that have been delivered.")
        return order

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def create(self, validated_data):
        user = self.context["request"].user
        validated_data["customer"] = user
        if validated_data.get("order") is None:
            # General (non-order) rating: one per customer per restaurant; re-posting edits it.
            review = RestaurantReview.objects.filter(
                restaurant=validated_data["restaurant"], customer=user, order__isnull=True
            ).first()
            if review:
                for field in ("rating", "food_quality_rating", "comment"):
                    if field in validated_data:
                        setattr(review, field, validated_data[field])
                review.save()
                return review
        return super().create(validated_data)

from rest_framework import serializers

from .models import Category, FavoriteMeal, Meal, MealImage, MealReview


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "is_active", "display_order"]


class MealListSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source="restaurant.name", read_only=True)
    restaurant_slug = serializers.CharField(source="restaurant.slug", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True, default=None)
    discounted_price = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    favorite_id = serializers.SerializerMethodField()

    class Meta:
        model = Meal
        fields = [
            "id", "name", "image", "price", "discount_percentage", "discounted_price", "packaging_fee", "ratings_count",
            "is_available", "preparation_time_minutes", "average_rating",
            "restaurant", "restaurant_name", "restaurant_slug", "category", "category_name",
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


class MealDetailSerializer(MealListSerializer):
    class Meta(MealListSerializer.Meta):
        fields = MealListSerializer.Meta.fields + [
            "description", "ingredients", "stock_quantity", "calories",
            "protein_grams", "carbs_grams", "fat_grams", "created_at",
        ]


class MealWriteSerializer(serializers.ModelSerializer):
    """Used by the owning vendor to manage their menu (spec §24)."""

    class Meta:
        model = Meal
        fields = [
            "id", "category", "name", "description", "ingredients", "image", "price",
            "discount_percentage", "packaging_fee", "preparation_time_minutes", "is_available",
            "stock_quantity", "calories", "protein_grams", "carbs_grams", "fat_grams",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        request = self.context["request"]
        restaurant = request.user.restaurant  # OneToOne — vendor must have a restaurant first
        return Meal.objects.create(restaurant=restaurant, **validated_data)


class MealImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MealImage
        fields = ["id", "image"]


class FavoriteMealSerializer(serializers.ModelSerializer):
    meal_detail = MealListSerializer(source="meal", read_only=True)

    class Meta:
        model = FavoriteMeal
        fields = ["id", "meal", "meal_detail", "created_at"]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        user = self.context["request"].user
        obj, _ = FavoriteMeal.objects.get_or_create(user=user, meal=validated_data["meal"])
        return obj


class MealReviewSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.full_name", read_only=True)
    customer_picture = serializers.ImageField(source="customer.profile_picture", read_only=True)

    class Meta:
        model = MealReview
        fields = ["id", "meal", "customer", "customer_name", "customer_picture", "rating", "comment", "created_at", "updated_at"]
        read_only_fields = ["id", "customer", "customer_name", "customer_picture", "created_at", "updated_at"]

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def create(self, validated_data):
        """One review per customer per meal: posting again updates the existing one."""
        user = self.context["request"].user
        review, _ = MealReview.objects.update_or_create(
            meal=validated_data["meal"], customer=user,
            defaults={"rating": validated_data["rating"], "comment": validated_data.get("comment", "")},
        )
        return review

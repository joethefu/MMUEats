import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from common.models import TimeStampedModel
from restaurants.models import Restaurant


class Category(TimeStampedModel):
    """Spec §32: Breakfast, Lunch, Dinner, Snacks, Fast Food, Beverages, Desserts,
    Healthy Meals, Vegetarian, Special Offers — admin-managed."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Meal(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="meals")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="meals")

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    ingredients = models.TextField(blank=True)
    image = models.ImageField(upload_to="meals/", null=True, blank=True)

    price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    discount_percentage = models.PositiveSmallIntegerField(default=0)  # 0-100
    # Takeaway container/packaging charge, added per unit ordered (KES). 0 = no charge.
    packaging_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    preparation_time_minutes = models.PositiveIntegerField(default=15)

    is_available = models.BooleanField(default=True)
    stock_quantity = models.PositiveIntegerField(null=True, blank=True)  # null = unlimited

    # Optional nutrition info (spec §24, §34)
    calories = models.PositiveIntegerField(null=True, blank=True)
    protein_grams = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    carbs_grams = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    fat_grams = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    ratings_count = models.PositiveIntegerField(default=0)
    order_count = models.PositiveIntegerField(default=0)  # for "Most Sold Meals" / trending

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["restaurant", "is_available"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.restaurant.name})"

    @property
    def discounted_price(self):
        if self.discount_percentage:
            from decimal import Decimal
            factor = Decimal(1) - (Decimal(self.discount_percentage) / Decimal(100))
            return (self.price * factor).quantize(Decimal("0.01"))
        return self.price

    @property
    def is_in_stock(self):
        return self.stock_quantity is None or self.stock_quantity > 0


class MealImage(TimeStampedModel):
    """Additional images per meal beyond the primary `image` field."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="meals/gallery/")

    def __str__(self):
        return f"Image for {self.meal.name}"


class FavoriteMeal(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorite_meals")
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name="favorited_by")

    class Meta:
        unique_together = ("user", "meal")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} ♥ {self.meal.name}"


class MealReview(TimeStampedModel):
    """A customer's 1-5 star rating and optional written review of a menu item.
    One review per customer per meal; submitting again edits the existing review."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name="reviews")
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="meal_reviews")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("meal", "customer")

    def __str__(self):
        return f"{self.rating}★ {self.meal.name} by {self.customer.email}"

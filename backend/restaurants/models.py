import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from common.models import TimeStampedModel


class Restaurant(TimeStampedModel):
    """
    A vendor's storefront. One-to-one with a User(role=vendor) — the vendor's
    dashboard operates on this model. Spec §22-23.
    """

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"
        TEMP_UNAVAILABLE = "temporarily_unavailable", "Temporarily Unavailable"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="restaurant")

    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to="restaurants/logos/", null=True, blank=True)
    banner = models.ImageField(upload_to="restaurants/banners/", null=True, blank=True)

    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    location = models.CharField(max_length=255)  # campus area, e.g. "Near Main Gate"

    opening_time = models.TimeField(null=True, blank=True)
    closing_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.CLOSED)

    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    average_delivery_minutes = models.PositiveIntegerField(default=30)

    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    ratings_count = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)  # admin can deactivate independent of vendor status

    class Meta:
        ordering = ["-average_rating", "name"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name

    @property
    def is_orderable(self):
        return self.is_active and self.status == self.Status.OPEN


class RestaurantImage(TimeStampedModel):
    """Additional gallery images beyond logo/banner (spec §7, §53)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="restaurants/gallery/")
    caption = models.CharField(max_length=150, blank=True)

    def __str__(self):
        return f"Image for {self.restaurant.name}"


class FavoriteRestaurant(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorite_restaurants")
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="favorited_by")

    class Meta:
        unique_together = ("user", "restaurant")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} ♥ {self.restaurant.name}"


class RestaurantReview(TimeStampedModel):
    """Spec §51: customers rate restaurants (and food quality) tied to a completed order."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="reviews")
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="restaurant_reviews")
    order = models.OneToOneField(
        "orders.Order", on_delete=models.CASCADE, related_name="restaurant_review", null=True, blank=True
    )
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    food_quality_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True
    )
    comment = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        # One review per order prevents fraudulent duplicate reviews (spec §51).
        constraints = [
            models.UniqueConstraint(
                fields=["order"], condition=models.Q(order__isnull=False), name="one_review_per_order"
            )
        ]

    def __str__(self):
        return f"{self.rating}★ — {self.restaurant.name} by {self.customer.email}"

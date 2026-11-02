from django.contrib import admin

from .models import FavoriteRestaurant, Restaurant, RestaurantImage, RestaurantReview


class RestaurantImageInline(admin.TabularInline):
    model = RestaurantImage
    extra = 0


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "status", "is_active", "average_rating", "ratings_count")
    list_filter = ("status", "is_active")
    search_fields = ("name", "owner__email", "location")
    inlines = [RestaurantImageInline]


@admin.register(RestaurantReview)
class RestaurantReviewAdmin(admin.ModelAdmin):
    list_display = ("restaurant", "customer", "rating", "created_at")
    list_filter = ("rating",)


admin.site.register(FavoriteRestaurant)

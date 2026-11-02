from django.contrib import admin

from .models import Category, FavoriteMeal, Meal, MealImage


class MealImageInline(admin.TabularInline):
    model = MealImage
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "display_order")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ("name", "restaurant", "category", "price", "is_available", "order_count")
    list_filter = ("is_available", "category")
    search_fields = ("name", "restaurant__name")
    inlines = [MealImageInline]


admin.site.register(FavoriteMeal)

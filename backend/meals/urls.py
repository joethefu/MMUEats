from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "meals"

router = DefaultRouter()
router.register("categories", views.CategoryViewSet, basename="category")
router.register("favorites", views.FavoriteMealViewSet, basename="favorite-meal")
router.register("reviews", views.MealReviewViewSet, basename="meal-review")
router.register("", views.MealViewSet, basename="meal")

urlpatterns = [
    path("", include(router.urls)),
]

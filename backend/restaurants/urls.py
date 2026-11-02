from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "restaurants"

router = DefaultRouter()
# NOTE: register specific-prefix routes BEFORE the catch-all "" (slug-based) route,
# otherwise Restaurant's `<slug>/` detail pattern shadows `favorites/`, `reviews/`, `mine/`.
router.register("favorites", views.FavoriteRestaurantViewSet, basename="favorite-restaurant")
router.register("reviews", views.RestaurantReviewViewSet, basename="restaurant-review")
router.register("mine", views.MyRestaurantView, basename="my-restaurant")
router.register("", views.RestaurantViewSet, basename="restaurant")

urlpatterns = [
    path("", include(router.urls)),
]

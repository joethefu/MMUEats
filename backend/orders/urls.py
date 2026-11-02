from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "orders"

router = DefaultRouter()
router.register("", views.OrderViewSet, basename="order")

urlpatterns = [
    path("cart/", views.CartView.as_view(), name="cart"),
    path("checkout/", views.CheckoutView.as_view(), name="checkout"),
    path("", include(router.urls)),
]

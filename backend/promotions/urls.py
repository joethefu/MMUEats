from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "promotions"

router = DefaultRouter()
router.register("coupons", views.CouponViewSet, basename="coupon")

urlpatterns = [
    path("coupons/validate/", views.ValidateCouponView.as_view(), name="validate-coupon"),
    path("", include(router.urls)),
]

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "users"

router = DefaultRouter()
router.register("delivery-locations", views.DeliveryLocationViewSet, basename="delivery-location")
router.register("vendor-applications", views.VendorApplicationViewSet, basename="vendor-application")
router.register("delivery-partner-applications", views.DeliveryPartnerApplicationViewSet, basename="delivery-partner-application")

urlpatterns = [
    path("me/", views.MeView.as_view(), name="me"),
    path("me/profile-picture/", views.ProfilePictureView.as_view(), name="me-profile-picture"),
    path("", include(router.urls)),
]

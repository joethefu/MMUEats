from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "deliveries"

router = DefaultRouter()
router.register("mine", views.MyDeliveriesViewSet, basename="my-delivery")
router.register("reviews", views.DeliveryPartnerReviewViewSet, basename="delivery-review")

urlpatterns = [
    path("profile/", views.MyDeliveryProfileView.as_view(), name="profile"),
    path("available/", views.AvailableDeliveriesView.as_view(), name="available"),
    path("earnings/", views.MyEarningsView.as_view(), name="earnings"),
    path("", include(router.urls)),
]

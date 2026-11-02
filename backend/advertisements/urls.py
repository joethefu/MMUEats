from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "advertisements"

router = DefaultRouter()
router.register("", views.AdvertisementViewSet, basename="advertisement")

urlpatterns = [
    path("active/", views.ActiveAdvertisementsView.as_view(), name="active"),
    path("<uuid:pk>/impression/", views.AdvertisementImpressionView.as_view(), name="impression"),
    path("<uuid:pk>/click/", views.AdvertisementClickView.as_view(), name="click"),
    path("", include(router.urls)),
]

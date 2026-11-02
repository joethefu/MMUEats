from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "payments"

router = DefaultRouter()
router.register("mine", views.MyPaymentsViewSet, basename="my-payment")

urlpatterns = [
    path("mpesa/stk-push/", views.MpesaSTKPushView.as_view(), name="mpesa-stk-push"),
    path("mpesa/callback/", views.MpesaCallbackView.as_view(), name="mpesa-callback"),
    path("mpesa/simulate/", views.SimulateMpesaCallbackView.as_view(), name="mpesa-simulate"),
    path("", include(router.urls)),
]

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView


def health_check(request):
    return JsonResponse({"status": "ok", "service": "MMUEats API"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check, name="health-check"),

    # API modules — each app owns its own urls.py
    path("api/auth/", include("authentication.urls")),
    path("api/users/", include("users.urls")),
    path("api/restaurants/", include("restaurants.urls")),
    path("api/meals/", include("meals.urls")),
    path("api/orders/", include("orders.urls")),
    path("api/payments/", include("payments.urls")),
    path("api/deliveries/", include("deliveries.urls")),
    path("api/notifications/", include("notifications.urls")),
    path("api/advertisements/", include("advertisements.urls")),
    path("api/promotions/", include("promotions.urls")),
    path("api/analytics/", include("analytics.urls")),

    # API docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

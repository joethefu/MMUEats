from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "analytics"

router = DefaultRouter()
router.register("admin/users", views.AdminUserManagementView, basename="admin-user")

urlpatterns = [
    path("vendor/dashboard/", views.VendorDashboardView.as_view(), name="vendor-dashboard"),
    path("vendor/sales-report/", views.VendorSalesReportView.as_view(), name="vendor-sales-report"),
    path("admin/dashboard/", views.AdminDashboardView.as_view(), name="admin-dashboard"),
    path("admin/audit-logs/", views.AuditLogListView.as_view(), name="admin-audit-logs"),
    path("", include(router.urls)),
]

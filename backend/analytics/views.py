from datetime import timedelta

from django.db.models import Avg, Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsAdministrator, IsVendor
from common.utils import write_audit_log
from meals.models import Meal
from orders.models import Order
from restaurants.models import Restaurant


class AdminDashboardView(APIView):
    """Spec §28-29: platform-wide admin dashboard statistics."""

    permission_classes = [IsAuthenticated, IsAdministrator]

    def get(self, request):
        from users.models import DeliveryPartnerApplication, User, VendorApplication

        today = timezone.localdate()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        orders = Order.objects.all()
        delivered = orders.filter(status=Order.Status.DELIVERED)

        def revenue_since(date):
            return delivered.filter(created_at__date__gte=date).aggregate(total=Sum("total"))["total"] or 0

        popular_meals = Meal.objects.filter(order_count__gt=0).order_by("-order_count").values("id", "name", "order_count")[:5]
        popular_restaurants = (
            Restaurant.objects.filter(is_active=True).order_by("-average_rating", "-ratings_count").values("id", "name", "average_rating", "ratings_count")[:5]
        )

        return Response({
            "total_users": User.objects.filter(role=User.Role.CUSTOMER).count(),
            "total_vendors": User.objects.filter(role=User.Role.VENDOR, is_approved=True).count(),
            "total_delivery_partners": User.objects.filter(role=User.Role.DELIVERY_PARTNER, is_approved=True).count(),
            "total_orders": orders.count(),
            "pending_orders": orders.filter(status=Order.Status.PENDING).count(),
            "completed_orders": delivered.count(),
            "cancelled_orders": orders.filter(status__in=[Order.Status.CANCELLED, Order.Status.REJECTED]).count(),
            "total_revenue": delivered.aggregate(total=Sum("total"))["total"] or 0,
            "daily_revenue": revenue_since(today),
            "weekly_revenue": revenue_since(week_ago),
            "monthly_revenue": revenue_since(month_ago),
            "popular_meals": list(popular_meals),
            "popular_restaurants": list(popular_restaurants),
            "pending_vendor_applications": VendorApplication.objects.filter(status="pending").count(),
            "pending_delivery_applications": DeliveryPartnerApplication.objects.filter(status="pending").count(),
        })


class AdminUserManagementView(viewsets.ReadOnlyModelViewSet):
    """Spec §28: admin oversight of all platform users, with suspend/reactivate."""

    permission_classes = [IsAuthenticated, IsAdministrator]

    def get_queryset(self):
        from users.models import User

        qs = User.objects.all().order_by("-created_at")
        role = self.request.query_params.get("role")
        if role:
            qs = qs.filter(role=role)
        return qs

    def get_serializer_class(self):
        from users.serializers import MeSerializer
        return MeSerializer

    @action(detail=True, methods=["post"])
    def suspend(self, request, pk=None):
        user = self.get_object()
        user.is_suspended = True
        user.save(update_fields=["is_suspended"])
        write_audit_log(request.user, "user_suspended", obj=user, request=request)
        return Response({"success": True, "message": f"{user.email} has been suspended."})

    @action(detail=True, methods=["post"])
    def reactivate(self, request, pk=None):
        user = self.get_object()
        user.is_suspended = False
        user.save(update_fields=["is_suspended"])
        write_audit_log(request.user, "user_reactivated", obj=user, request=request)
        return Response({"success": True, "message": f"{user.email} has been reactivated."})


class AuditLogListView(APIView):
    """Spec §71: admin-only view of recorded administrative actions."""

    permission_classes = [IsAuthenticated, IsAdministrator]

    def get(self, request):
        from common.models import AuditLog

        logs = AuditLog.objects.select_related("actor").all()[:200]
        return Response([
            {
                "id": str(log.id),
                "actor": log.actor.email if log.actor else None,
                "action": log.action,
                "object_type": log.object_type,
                "object_id": log.object_id,
                "metadata": log.metadata,
                "created_at": log.created_at,
            }
            for log in logs
        ])


class VendorDashboardView(APIView):
    """
    Spec §22: vendor dashboard statistics — today's orders, revenue, pending/
    completed/cancelled counts, most-sold meals, ratings.
    """

    permission_classes = [IsAuthenticated, IsVendor]

    def get(self, request):
        try:
            restaurant = Restaurant.objects.get(owner=request.user)
        except Restaurant.DoesNotExist:
            return Response(
                {"error": {"code": "not_found", "message": "Set up your restaurant profile first."}}, status=404
            )

        today = timezone.localdate()
        orders = Order.objects.filter(restaurant=restaurant)
        today_orders = orders.filter(created_at__date=today)

        today_revenue = today_orders.filter(status=Order.Status.DELIVERED).aggregate(total=Sum("total"))["total"] or 0
        pending_count = orders.filter(status=Order.Status.PENDING).count()
        completed_count = orders.filter(status=Order.Status.DELIVERED).count()
        cancelled_count = orders.filter(status__in=[Order.Status.CANCELLED, Order.Status.REJECTED]).count()

        most_sold = (
            Meal.objects.filter(restaurant=restaurant)
            .order_by("-order_count")
            .values("id", "name", "order_count")[:5]
        )

        return Response({
            "restaurant_name": restaurant.name,
            "restaurant_status": restaurant.status,
            "today_orders_count": today_orders.count(),
            "today_revenue": today_revenue,
            "pending_orders_count": pending_count,
            "completed_orders_count": completed_count,
            "cancelled_orders_count": cancelled_count,
            "most_sold_meals": list(most_sold),
            "average_rating": restaurant.average_rating,
            "ratings_count": restaurant.ratings_count,
        })


class VendorSalesReportView(APIView):
    """
    Spec §52: vendor reports — daily/monthly sales, meal performance, revenue,
    orders, filtered by optional ?start_date=&end_date= (YYYY-MM-DD).
    """

    permission_classes = [IsAuthenticated, IsVendor]

    def get(self, request):
        try:
            restaurant = Restaurant.objects.get(owner=request.user)
        except Restaurant.DoesNotExist:
            return Response(
                {"error": {"code": "not_found", "message": "Set up your restaurant profile first."}}, status=404
            )

        end_date = request.query_params.get("end_date")
        start_date = request.query_params.get("start_date")
        today = timezone.localdate()

        end = timezone.datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else today
        start = timezone.datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else end - timedelta(days=29)

        orders = Order.objects.filter(
            restaurant=restaurant, created_at__date__gte=start, created_at__date__lte=end
        )
        delivered = orders.filter(status=Order.Status.DELIVERED)

        # Daily sales series for the requested range.
        daily = (
            delivered.annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(revenue=Sum("total"), order_count=Count("id"))
            .order_by("day")
        )

        meal_performance = (
            Meal.objects.filter(restaurant=restaurant, order_count__gt=0)
            .order_by("-order_count")
            .values("id", "name", "order_count", "average_rating")[:20]
        )

        summary = delivered.aggregate(total_revenue=Sum("total"), total_orders=Count("id"))

        return Response({
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "total_revenue": summary["total_revenue"] or 0,
            "total_orders": summary["total_orders"] or 0,
            "daily_sales": list(daily),
            "meal_performance": list(meal_performance),
        })

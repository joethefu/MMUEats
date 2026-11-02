from django.db.models import Sum
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsDeliveryPartner
from orders.models import Order
from .models import Delivery, DeliveryPartnerProfile, DeliveryPartnerReview
from .serializers import DeliveryPartnerProfileSerializer, DeliveryPartnerReviewSerializer, DeliverySerializer


class MyDeliveryProfileView(APIView):
    """GET/PATCH the logged-in delivery partner's profile, incl. online/offline toggle (spec §27)."""

    permission_classes = [IsAuthenticated, IsDeliveryPartner]

    def get_profile(self, user):
        profile, _ = DeliveryPartnerProfile.objects.get_or_create(user=user)
        return profile

    def get(self, request):
        return Response(DeliveryPartnerProfileSerializer(self.get_profile(request.user)).data)

    def patch(self, request):
        profile = self.get_profile(request.user)
        serializer = DeliveryPartnerProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class AvailableDeliveriesView(APIView):
    """Spec §26-27: unassigned deliveries an online, approved partner can accept."""

    permission_classes = [IsAuthenticated, IsDeliveryPartner]

    def get(self, request):
        deliveries = Delivery.objects.filter(
            delivery_partner__isnull=True, order__status=Order.Status.READY_FOR_PICKUP
        ).select_related("order", "order__restaurant", "order__customer")
        return Response(DeliverySerializer(deliveries, many=True).data)


class MyDeliveriesViewSet(viewsets.ReadOnlyModelViewSet):
    """Current + history deliveries for the logged-in partner (spec §26)."""

    serializer_class = DeliverySerializer
    permission_classes = [IsAuthenticated, IsDeliveryPartner]

    def get_queryset(self):
        return Delivery.objects.filter(delivery_partner=self.request.user).select_related(
            "order", "order__restaurant", "order__customer"
        )

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        try:
            delivery = Delivery.objects.select_related("order").get(
                pk=pk, delivery_partner__isnull=True, order__status=Order.Status.READY_FOR_PICKUP
            )
        except Delivery.DoesNotExist:
            return Response(
                {"error": {"code": "not_found", "message": "This delivery is no longer available."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        delivery.delivery_partner = request.user
        delivery.accepted_at = timezone.now()
        delivery.save()

        from notifications.services import notify_user
        from notifications.models import Notification
        notify_user(
            delivery.order.customer,
            Notification.Type.DELIVERY_PARTNER_ASSIGNED,
            "Delivery partner assigned",
            f"{request.user.full_name} is picking up order #{delivery.order.order_number}.",
            data={"order_id": str(delivery.order.id)},
        )

        return Response(DeliverySerializer(delivery).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        """Spec §27: reject a delivery — releases it back to the pool if not yet picked up."""
        delivery = self.get_object()
        if delivery.picked_up_at is not None:
            return Response(
                {"error": {"code": "too_late", "message": "This delivery has already been picked up."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        delivery.delivery_partner = None
        delivery.accepted_at = None
        delivery.save()
        return Response({"success": True, "message": "Delivery released back to the available pool."})


class MyEarningsView(APIView):
    """Spec §26-27, §52: earnings summary for the logged-in delivery partner."""

    permission_classes = [IsAuthenticated, IsDeliveryPartner]

    def get(self, request):
        profile, _ = DeliveryPartnerProfile.objects.get_or_create(user=request.user)
        completed = Delivery.objects.filter(delivery_partner=request.user, delivered_at__isnull=False)
        today = timezone.localdate()
        today_earnings = completed.filter(delivered_at__date=today).aggregate(total=Sum("earnings"))["total"] or 0

        return Response({
            "total_earnings": profile.total_earnings,
            "total_deliveries": profile.total_deliveries,
            "today_earnings": today_earnings,
            "today_deliveries": completed.filter(delivered_at__date=today).count(),
            "average_rating": profile.average_rating,
            "ratings_count": profile.ratings_count,
        })


class DeliveryPartnerReviewViewSet(viewsets.ModelViewSet):
    serializer_class = DeliveryPartnerReviewSerializer
    http_method_names = ["get", "post"]

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return DeliveryPartnerReview.objects.filter(customer=self.request.user)

    def perform_create(self, serializer):
        review = serializer.save()
        partner = review.delivery_partner
        if partner:
            profile, _ = DeliveryPartnerProfile.objects.get_or_create(user=partner)
            from django.db.models import Avg, Count
            stats = DeliveryPartnerReview.objects.filter(delivery_partner=partner).aggregate(
                avg=Avg("speed_rating"), count=Count("id")
            )
            profile.average_rating = round(stats["avg"] or 0, 2)
            profile.ratings_count = stats["count"]
            profile.save(update_fields=["average_rating", "ratings_count"])

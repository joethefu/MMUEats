from django.db.models import Count
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsAdministrator
from .models import Advertisement, AdvertisementClick, AdvertisementImpression
from .serializers import AdvertisementAdminSerializer, AdvertisementPublicSerializer, TrackingEventSerializer


class AdvertisementViewSet(viewsets.ModelViewSet):
    """Spec §44: full admin CRUD for advertisements."""

    queryset = Advertisement.objects.all()
    serializer_class = AdvertisementAdminSerializer
    permission_classes = [IsAuthenticated, IsAdministrator]

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated, IsAdministrator])
    def analytics(self, request, pk=None):
        """Spec §46: impressions, clicks, CTR for one advertisement."""
        ad = self.get_object()
        impressions = ad.impressions.count()
        clicks = ad.clicks.count()
        ctr = round((clicks / impressions) * 100, 2) if impressions else 0
        return Response({
            "advertisement_id": str(ad.id),
            "title": ad.title,
            "impressions": impressions,
            "clicks": clicks,
            "ctr_percent": ctr,
            "start_date": ad.start_date,
            "end_date": ad.end_date,
            "is_active": ad.is_active,
        })


class ActiveAdvertisementsView(APIView):
    """
    Spec §45: publicly readable — only active ads within their scheduled date
    range for the requested placement, highest priority first. The frontend's
    once-per-day logic (localStorage) decides whether to actually display one;
    this endpoint just returns what's currently eligible.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        placement = request.query_params.get("placement", Advertisement.Placement.STARTUP_POPUP)
        today = timezone.localdate()
        ads = Advertisement.objects.filter(
            placement=placement, is_active=True, start_date__lte=today, end_date__gte=today
        )
        return Response(AdvertisementPublicSerializer(ads, many=True).data)


class AdvertisementImpressionView(APIView):
    """Spec §46-47: log an impression. AllowAny — ads are shown to logged-out visitors too."""

    permission_classes = [AllowAny]

    def post(self, request, pk):
        try:
            ad = Advertisement.objects.get(pk=pk)
        except Advertisement.DoesNotExist:
            return Response({"error": {"code": "not_found", "message": "Advertisement not found."}}, status=404)

        serializer = TrackingEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        AdvertisementImpression.objects.create(
            advertisement=ad,
            user=request.user if request.user.is_authenticated else None,
            device_id=serializer.validated_data["device_id"],
            platform=serializer.validated_data["platform"],
        )
        return Response({"success": True}, status=status.HTTP_201_CREATED)


class AdvertisementClickView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, pk):
        try:
            ad = Advertisement.objects.get(pk=pk)
        except Advertisement.DoesNotExist:
            return Response({"error": {"code": "not_found", "message": "Advertisement not found."}}, status=404)

        serializer = TrackingEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        AdvertisementClick.objects.create(
            advertisement=ad,
            user=request.user if request.user.is_authenticated else None,
            device_id=serializer.validated_data["device_id"],
            destination_url=ad.external_url,
            platform=serializer.validated_data["platform"],
        )
        return Response({"success": True, "destination_url": ad.external_url}, status=status.HTTP_201_CREATED)

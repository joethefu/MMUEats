from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsAdministrator
from restaurants.models import Restaurant
from .models import Coupon
from .serializers import CouponAdminSerializer, CouponValidateSerializer
from .services import CouponError, validate_and_price_coupon


class CouponViewSet(viewsets.ModelViewSet):
    """Spec §50: admin manages all coupons."""

    queryset = Coupon.objects.all()
    serializer_class = CouponAdminSerializer
    permission_classes = [IsAuthenticated, IsAdministrator]


class ValidateCouponView(APIView):
    """Customer-facing: preview a coupon's discount before checkout, without redeeming it."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CouponValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            restaurant = Restaurant.objects.get(pk=data["restaurant_id"])
        except Restaurant.DoesNotExist:
            return Response({"error": {"code": "not_found", "message": "Restaurant not found."}}, status=404)

        try:
            coupon, discount_amount, free_delivery = validate_and_price_coupon(
                data["code"], request.user, restaurant, data["subtotal"], data["delivery_fee"]
            )
        except CouponError as exc:
            return Response({"error": {"code": exc.code, "message": exc.message}}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "valid": True,
            "code": coupon.code,
            "discount_amount": discount_amount,
            "free_delivery": free_delivery,
            "description": coupon.description,
        })

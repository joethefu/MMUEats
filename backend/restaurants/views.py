from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from common.permissions import IsVendor
from .models import FavoriteRestaurant, Restaurant, RestaurantImage, RestaurantReview
from .serializers import (
    FavoriteRestaurantSerializer,
    RestaurantDetailSerializer,
    RestaurantImageSerializer,
    RestaurantListSerializer,
    RestaurantReviewSerializer,
    RestaurantWriteSerializer,
)


class RestaurantViewSet(viewsets.ModelViewSet):
    """
    Public browsing (spec §33): list/retrieve open to everyone.
    Create/update/delete restricted to the owning vendor.
    """

    queryset = Restaurant.objects.filter(is_active=True).prefetch_related("favorited_by")
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status"]
    search_fields = ["name", "location", "description"]
    ordering_fields = ["average_rating", "average_delivery_minutes", "created_at"]
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action == "retrieve":
            return RestaurantDetailSerializer
        if self.action in ("create", "update", "partial_update"):
            return RestaurantWriteSerializer
        return RestaurantListSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        if self.action == "create":
            return [IsAuthenticated(), IsVendor()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action in ("update", "partial_update", "destroy"):
            # Vendors only ever touch their own restaurant; admins can touch any.
            if self.request.user.role != "admin":
                qs = qs.filter(owner=self.request.user)
        return qs

    def perform_update(self, serializer):
        if self.request.user.role not in ("admin",) and serializer.instance.owner_id != self.request.user.id:
            raise PermissionError("Not your restaurant.")
        serializer.save()


class MyRestaurantView(viewsets.ViewSet):
    """Convenience endpoint: GET the logged-in vendor's own restaurant profile."""

    permission_classes = [IsAuthenticated, IsVendor]

    def list(self, request):
        try:
            restaurant = Restaurant.objects.get(owner=request.user)
        except Restaurant.DoesNotExist:
            return Response({"error": {"code": "not_found", "message": "No restaurant profile yet."}}, status=404)
        return Response(RestaurantDetailSerializer(restaurant, context={"request": request}).data)


class FavoriteRestaurantViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteRestaurantSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "delete"]

    def get_queryset(self):
        return FavoriteRestaurant.objects.filter(user=self.request.user).select_related("restaurant")


class RestaurantReviewViewSet(viewsets.ModelViewSet):
    serializer_class = RestaurantReviewSerializer
    http_method_names = ["get", "post"]

    def get_queryset(self):
        qs = RestaurantReview.objects.select_related("customer")
        restaurant_id = self.request.query_params.get("restaurant")
        if restaurant_id:
            qs = qs.filter(restaurant_id=restaurant_id)
        return qs

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated()]
        return [AllowAny()]

    def perform_create(self, serializer):
        review = serializer.save()
        # Recalculate restaurant's aggregate rating.
        from django.db.models import Avg, Count

        restaurant = review.restaurant
        stats = restaurant.reviews.aggregate(avg=Avg("rating"), count=Count("id"))
        restaurant.average_rating = round(stats["avg"] or 0, 2)
        restaurant.ratings_count = stats["count"]
        restaurant.save(update_fields=["average_rating", "ratings_count"])

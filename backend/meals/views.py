from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg, Count
from rest_framework import filters, mixins, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated

from common.permissions import IsAdministrator, IsVendor
from common.permissions import IsCustomer
from .models import Category, FavoriteMeal, Meal, MealReview
from .serializers import (
    CategorySerializer,
    FavoriteMealSerializer,
    MealDetailSerializer,
    MealListSerializer,
    MealReviewSerializer,
    MealWriteSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    """Spec §32: admin-managed food categories, publicly readable."""

    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        return [IsAuthenticated(), IsAdministrator()]


class MealViewSet(viewsets.ModelViewSet):
    """
    Public browsing/search (spec §48). Vendors manage only meals under their own
    restaurant — enforced both in queryset scoping and MealWriteSerializer.create.
    """

    queryset = Meal.objects.select_related("restaurant", "category").filter(
        is_available=True, restaurant__is_active=True
    )
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["restaurant", "category", "is_available"]
    search_fields = ["name", "description", "ingredients"]
    ordering_fields = ["price", "average_rating", "order_count", "created_at"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return MealDetailSerializer
        if self.action in ("create", "update", "partial_update"):
            return MealWriteSerializer
        return MealListSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        return [IsAuthenticated(), IsVendor()]

    def get_queryset(self):
        qs = Meal.objects.select_related("restaurant", "category")
        if self.action in ("list", "retrieve") and not (
            self.request.user.is_authenticated and self.request.user.role in ("vendor", "admin")
        ):
            qs = qs.filter(is_available=True, restaurant__is_active=True)
        if self.action in ("update", "partial_update", "destroy") and self.request.user.role != "admin":
            qs = qs.filter(restaurant__owner=self.request.user)
        return qs


class FavoriteMealViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteMealSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "delete"]

    def get_queryset(self):
        return FavoriteMeal.objects.filter(user=self.request.user).select_related("meal")


class MealReviewViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """Ratings + written reviews of menu items. Anyone can read; only customers can write,
    and each customer has at most one review per meal (re-posting edits it)."""

    serializer_class = MealReviewSerializer

    def get_queryset(self):
        qs = MealReview.objects.select_related("customer")
        meal_id = self.request.query_params.get("meal")
        if meal_id:
            qs = qs.filter(meal_id=meal_id)
        if self.action == "destroy":
            qs = qs.filter(customer=self.request.user)
        return qs

    def get_permissions(self):
        if self.action == "list":
            return [AllowAny()]
        return [IsAuthenticated(), IsCustomer()]

    @staticmethod
    def recalculate(meal):
        stats = meal.reviews.aggregate(avg=Avg("rating"), count=Count("id"))
        meal.average_rating = round(stats["avg"] or 0, 2)
        meal.ratings_count = stats["count"]
        meal.save(update_fields=["average_rating", "ratings_count"])

    def perform_create(self, serializer):
        review = serializer.save()
        self.recalculate(review.meal)

    def perform_destroy(self, instance):
        meal = instance.meal
        instance.delete()
        self.recalculate(meal)

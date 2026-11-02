from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

from authentication.models import PasswordResetToken
from authentication.tasks import send_partner_approved_email, send_partner_rejected_email
from common.permissions import IsAdministrator, IsOwnerOrAdmin
from common.utils import write_audit_log
from .models import DeliveryLocation, DeliveryPartnerApplication, User, VendorApplication
from .serializers import (
    ApplicationReviewSerializer,
    DeliveryLocationSerializer,
    DeliveryPartnerApplicationSerializer,
    MeSerializer,
    VendorApplicationSerializer,
)


class MeView(APIView):
    """GET current user profile, PATCH to update editable fields (spec §21: manage profile)."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        return Response(MeSerializer(request.user, context={"request": request}).data)

    def patch(self, request):
        user = request.user
        old_picture = user.profile_picture.name if user.profile_picture else None
        serializer = MeSerializer(user, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # Don't leave orphaned files behind when the picture is replaced.
        if "profile_picture" in request.FILES and old_picture and old_picture != user.profile_picture.name:
            user.profile_picture.storage.delete(old_picture)
        return Response(serializer.data)


class ProfilePictureView(APIView):
    """DELETE removes the current user's profile picture (falls back to initials in the UI)."""

    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        if user.profile_picture:
            user.profile_picture.delete(save=False)
            user.profile_picture = None
            user.save(update_fields=["profile_picture"])
        return Response(MeSerializer(user, context={"request": request}).data)


class DeliveryLocationViewSet(viewsets.ModelViewSet):
    """Customers can save multiple delivery locations (spec §21, §36)."""

    serializer_class = DeliveryLocationSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        return DeliveryLocation.objects.filter(user=self.request.user)


def _generate_username(email):
    return email


def _approve_application(application, role, name_field, reviewer, notes, request):
    """Shared approve logic for vendor/delivery-partner applications."""
    email = application.email.strip().lower()
    full_name = getattr(application, name_field)

    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            "username": _generate_username(email),
            "full_name": full_name,
            "phone_number": application.phone_number,
            "role": role,
            "is_email_verified": True,  # already vetted by admin review
        },
    )
    if not created:
        user.role = role
    user.is_approved = True
    user.is_suspended = False
    user.set_unusable_password()
    user.save()

    application.status = "approved"
    application.reviewed_by = reviewer
    application.reviewed_at = timezone.now()
    application.review_notes = notes
    application.resulting_user = user
    application.save()

    PasswordResetToken.objects.filter(user=user, used_at__isnull=True).update(used_at=timezone.now())
    token_obj = PasswordResetToken.objects.create(user=user)
    role_label = "Vendor" if role == User.Role.VENDOR else "Delivery Partner"
    send_partner_approved_email.delay(user.email, user.full_name, role_label, token_obj.token)

    from notifications.services import notify_user
    from notifications.models import Notification
    notify_user(
        user, Notification.Type.VENDOR_APPLICATION_STATUS if role == User.Role.VENDOR else Notification.Type.DELIVERY_APPLICATION_STATUS,
        f"You're approved as a {role_label}!",
        "Set your password to get started — check your email for the link.",
    )

    write_audit_log(reviewer, f"{role}_application_approved", obj=application, request=request)
    return user


class VendorApplicationViewSet(viewsets.ModelViewSet):
    """
    Spec §17, §30: public submission (AllowAny on create), admin-only review.
    Vendor accounts only become usable after admin approval here.
    """

    queryset = VendorApplication.objects.all()
    serializer_class = VendorApplicationSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filterset_fields = ["status"]

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        return [IsAuthenticated(), IsAdministrator()]

    @action(detail=True, methods=["post"])
    def review(self, request, pk=None):
        application = self.get_object()
        serializer = ApplicationReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action_value = serializer.validated_data["action"]
        notes = serializer.validated_data.get("notes", "")

        if application.status == "approved":
            return Response(
                {"error": {"code": "conflict", "message": "This application has already been approved."}},
                status=status.HTTP_409_CONFLICT,
            )

        if action_value == "approve":
            _approve_application(application, User.Role.VENDOR, "owner_name", request.user, notes, request)
        elif action_value == "reject":
            application.status = "rejected"
            application.reviewed_by = request.user
            application.reviewed_at = timezone.now()
            application.review_notes = notes
            application.save()
            send_partner_rejected_email.delay(application.email, application.owner_name, "Vendor", notes)
            write_audit_log(request.user, "vendor_application_rejected", obj=application, request=request)
        else:  # needs_info
            application.status = "needs_info"
            application.reviewed_by = request.user
            application.reviewed_at = timezone.now()
            application.review_notes = notes
            application.save()
            write_audit_log(request.user, "vendor_application_needs_info", obj=application, request=request)

        return Response(VendorApplicationSerializer(application).data)


class DeliveryPartnerApplicationViewSet(viewsets.ModelViewSet):
    """Spec §18, §31: public submission, admin-only review."""

    queryset = DeliveryPartnerApplication.objects.all()
    serializer_class = DeliveryPartnerApplicationSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filterset_fields = ["status"]

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        return [IsAuthenticated(), IsAdministrator()]

    @action(detail=True, methods=["post"])
    def review(self, request, pk=None):
        application = self.get_object()
        serializer = ApplicationReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action_value = serializer.validated_data["action"]
        notes = serializer.validated_data.get("notes", "")

        if application.status == "approved":
            return Response(
                {"error": {"code": "conflict", "message": "This application has already been approved."}},
                status=status.HTTP_409_CONFLICT,
            )

        if action_value == "approve":
            _approve_application(application, User.Role.DELIVERY_PARTNER, "full_name", request.user, notes, request)
        elif action_value == "reject":
            application.status = "rejected"
            application.reviewed_by = request.user
            application.reviewed_at = timezone.now()
            application.review_notes = notes
            application.save()
            send_partner_rejected_email.delay(application.email, application.full_name, "Delivery Partner", notes)
            write_audit_log(request.user, "delivery_partner_application_rejected", obj=application, request=request)
        else:  # needs_info
            application.status = "needs_info"
            application.reviewed_by = request.user
            application.reviewed_at = timezone.now()
            application.review_notes = notes
            application.save()
            write_audit_log(request.user, "delivery_partner_application_needs_info", obj=application, request=request)

        return Response(DeliveryPartnerApplicationSerializer(application).data)

import logging

from django.core.cache import cache
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from common.utils import generate_secure_token, mask_token, write_audit_log
from users.models import User

from .models import EmailVerificationToken, PasswordResetToken
from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    ResendVerificationSerializer,
    UserPublicSerializer,
    VerifyEmailSerializer,
)
from .tasks import send_password_reset_email, send_verification_email

logger = logging.getLogger("django")


def issue_tokens_for(user):
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


class RegisterView(APIView):
    """Customer-only sign up. See RegisterSerializer for why vendor/delivery are excluded."""

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "register"

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        token_obj = EmailVerificationToken.objects.create(user=user)
        send_verification_email.delay(user.email, user.full_name, token_obj.token)
        logger.info("New customer registered: %s (verification token=%s)", user.email, mask_token(token_obj.token))

        return Response(
            {
                "success": True,
                "message": "Account created. Please check your email to verify your address.",
                "user": UserPublicSerializer(user, context={"request": request}).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        tokens = issue_tokens_for(user)
        return Response(
            {"success": True, **tokens, "user": UserPublicSerializer(user, context={"request": request}).data},
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response({"error": {"code": "validation_error", "message": "Refresh token is required."}}, status=400)
        try:
            RefreshToken(refresh).blacklist()
        except TokenError:
            pass  # already invalid/expired — logout should still succeed idempotently
        return Response({"success": True, "message": "Logged out."})


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token_value = serializer.validated_data["token"]

        try:
            token_obj = EmailVerificationToken.objects.select_related("user").get(token=token_value)
        except EmailVerificationToken.DoesNotExist:
            return Response(
                {"error": {"code": "invalid_token", "message": "This verification link is invalid."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if token_obj.is_used:
            return Response(
                {"error": {"code": "invalid_token", "message": "This verification link has already been used."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if token_obj.is_expired:
            return Response(
                {"error": {"code": "token_expired", "message": "This verification link has expired."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = token_obj.user
        user.is_email_verified = True
        user.save(update_fields=["is_email_verified"])
        token_obj.mark_used()

        # Invalidate any other outstanding verification tokens for this user.
        EmailVerificationToken.objects.filter(user=user, used_at__isnull=True).exclude(pk=token_obj.pk).update(
            used_at=timezone.now()
        )

        return Response({"success": True, "message": "Email verified. You can now log in."})


class ResendVerificationView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "resend-verification"

    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].strip().lower()

        generic_response = Response(
            {"success": True, "message": "If an unverified account exists for that email, a new link has been sent."}
        )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return generic_response  # don't leak whether an email is registered

        if user.is_email_verified:
            return generic_response

        cooldown_key = f"resend-verification:{user.id}"
        if cache.get(cooldown_key):
            return generic_response  # rate-limited silently — same response either way
        cache.set(cooldown_key, True, timeout=60)

        # Invalidate previous tokens, issue a fresh one.
        EmailVerificationToken.objects.filter(user=user, used_at__isnull=True).update(used_at=timezone.now())
        token_obj = EmailVerificationToken.objects.create(user=user)
        send_verification_email.delay(user.email, user.full_name, token_obj.token)
        logger.info("Verification email resent to %s (token=%s)", user.email, mask_token(token_obj.token))

        return generic_response


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password-reset"

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].strip().lower()

        generic_response = Response(
            {"success": True, "message": "If an account exists for that email, a reset link has been sent."}
        )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return generic_response

        PasswordResetToken.objects.filter(user=user, used_at__isnull=True).update(used_at=timezone.now())
        token_obj = PasswordResetToken.objects.create(user=user)
        send_password_reset_email.delay(user.email, user.full_name, token_obj.token)
        logger.info("Password reset email sent to %s (token=%s)", user.email, mask_token(token_obj.token))

        return generic_response


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token_value = serializer.validated_data["token"]

        try:
            token_obj = PasswordResetToken.objects.select_related("user").get(token=token_value)
        except PasswordResetToken.DoesNotExist:
            return Response(
                {"error": {"code": "invalid_token", "message": "This reset link is invalid."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if token_obj.is_used:
            return Response(
                {"error": {"code": "invalid_token", "message": "This reset link has already been used."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if token_obj.is_expired:
            return Response(
                {"error": {"code": "token_expired", "message": "This reset link has expired."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = token_obj.user
        user.set_password(serializer.validated_data["password"])
        user.save(update_fields=["password"])
        token_obj.mark_used()

        return Response({"success": True, "message": "Password reset successfully. You can now log in."})


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user

        if not user.check_password(serializer.validated_data["old_password"]):
            return Response(
                {"error": {"code": "invalid_password", "message": "Current password is incorrect."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        write_audit_log(user, "password_changed", obj=user, request=request)

        # Invalidate every existing session so the user must log in again with the new password.
        from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

        for outstanding in OutstandingToken.objects.filter(user=user):
            BlacklistedToken.objects.get_or_create(token=outstanding)

        return Response(
            {"success": True, "message": "Password changed successfully. Please log in again.", "logout_required": True}
        )

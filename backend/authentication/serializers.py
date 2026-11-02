from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from users.models import User


class UserPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "full_name", "email", "phone_number", "role",
            "is_email_verified", "is_approved", "profile_picture", "created_at",
        ]
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    """
    Customer-only registration (spec §9-10). Vendor/Delivery accounts are created
    through the separate partner-application + admin-approval flow (Phase 3),
    never through this endpoint.
    """

    confirm_password = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["full_name", "email", "phone_number", "password", "confirm_password"]

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        # Deliberately NOT restricting to any university domain — see spec §9.
        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("confirm_password"):
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(
            username=validated_data["email"],
            role=User.Role.CUSTOMER,
            is_email_verified=False,
            **validated_data,
        )
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        email = attrs["email"].strip().lower()
        user = authenticate(username=email, password=attrs["password"])

        if user is None:
            # Distinguish "wrong credentials" from "right credentials, unverified"
            # only after confirming the account+password actually match, so we
            # never leak whether an email is registered via a different error.
            raise serializers.ValidationError(
                {"detail": "Invalid email or password."}, code="invalid_credentials"
            )

        if user.is_suspended or not user.is_active:
            raise serializers.ValidationError(
                {"detail": "This account has been suspended. Contact support."}, code="suspended"
            )

        if not user.is_email_verified:
            raise serializers.ValidationError(
                {"detail": "Please verify your email address before logging in."},
                code="email_not_verified",
            )

        attrs["user"] = user
        return attrs


class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()


class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.CharField()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs

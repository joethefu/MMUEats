"""
Central role-based permission classes.

Role checks always happen server-side here — the frontend route guards are a
UX convenience only and must never be relied on for real access control.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsCustomer(BasePermission):
    message = "This action is only available to customers."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "customer")


class IsVendor(BasePermission):
    message = "This action is only available to approved vendors."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "vendor"
            and request.user.is_approved
        )


class IsDeliveryPartner(BasePermission):
    message = "This action is only available to approved delivery partners."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "delivery_partner"
            and request.user.is_approved
        )


class IsAdministrator(BasePermission):
    message = "This action is only available to administrators."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "admin")


class IsOwnerOrAdmin(BasePermission):
    """Object-level permission: only the owning user (via `owner_field`) or an admin."""

    owner_field = "user"
    message = "You do not have permission to access this resource."

    def has_object_permission(self, request, view, obj):
        if request.user.role == "admin":
            return True
        owner = getattr(obj, self.owner_field, None)
        return owner == request.user


class ReadOnlyOrAdmin(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.role == "admin")

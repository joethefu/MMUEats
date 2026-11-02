from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import DeliveryLocation, DeliveryPartnerApplication, User, VendorApplication


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("-created_at",)
    list_display = ("email", "full_name", "role", "is_email_verified", "is_approved", "is_suspended", "is_active")
    list_filter = ("role", "is_email_verified", "is_approved", "is_suspended", "is_active")
    search_fields = ("email", "full_name", "phone_number")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("full_name", "username", "phone_number", "profile_picture")}),
        ("Role & status", {"fields": ("role", "is_email_verified", "is_approved", "is_suspended")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "username", "full_name", "role", "password1", "password2"),
        }),
    )


@admin.register(DeliveryLocation)
class DeliveryLocationAdmin(admin.ModelAdmin):
    list_display = ("label", "campus_location", "user", "is_default")
    list_filter = ("campus_location", "is_default")
    search_fields = ("label", "user__email")


@admin.register(VendorApplication)
class VendorApplicationAdmin(admin.ModelAdmin):
    list_display = ("business_name", "owner_name", "email", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("business_name", "owner_name", "email")


@admin.register(DeliveryPartnerApplication)
class DeliveryPartnerApplicationAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "preferred_area", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("full_name", "email")

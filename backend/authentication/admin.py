from django.contrib import admin

from .models import EmailVerificationToken, PasswordResetToken


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "expires_at", "used_at")
    search_fields = ("user__email",)
    readonly_fields = [f.name for f in EmailVerificationToken._meta.fields]


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "expires_at", "used_at")
    search_fields = ("user__email",)
    readonly_fields = [f.name for f in PasswordResetToken._meta.fields]

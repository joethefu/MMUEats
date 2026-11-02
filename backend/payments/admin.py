from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "method", "status", "amount", "mpesa_receipt_number", "is_mocked", "created_at")
    list_filter = ("method", "status", "is_mocked")
    search_fields = ("order__order_number", "mpesa_receipt_number", "checkout_request_id")
    readonly_fields = ["raw_callback"]

from django.contrib import admin

from .models import Cart, CartItem, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = [f.name for f in OrderItem._meta.fields]
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "customer", "restaurant", "status", "payment_status", "total", "created_at")
    list_filter = ("status", "payment_method", "payment_status")
    search_fields = ("order_number", "customer__email", "restaurant__name")
    inlines = [OrderItemInline]


admin.site.register(Cart)
admin.site.register(CartItem)

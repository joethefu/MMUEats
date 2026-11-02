from django.contrib import admin

from .models import Delivery, DeliveryPartnerProfile, DeliveryPartnerReview


@admin.register(DeliveryPartnerProfile)
class DeliveryPartnerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "is_online", "total_deliveries", "total_earnings", "average_rating")
    list_filter = ("is_online",)


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ("order", "delivery_partner", "accepted_at", "delivered_at", "earnings")
    list_filter = ("delivery_partner",)


admin.site.register(DeliveryPartnerReview)

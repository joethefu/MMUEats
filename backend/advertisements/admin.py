from django.contrib import admin

from .models import Advertisement, AdvertisementClick, AdvertisementImpression


@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ("title", "placement", "is_active", "start_date", "end_date", "priority")
    list_filter = ("placement", "is_active")
    search_fields = ("title",)


admin.site.register(AdvertisementImpression)
admin.site.register(AdvertisementClick)

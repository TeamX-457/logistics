from django.contrib import admin

from .models import Location


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("delivery", "latitude", "longitude", "timestamp")
    list_filter = ("delivery",)

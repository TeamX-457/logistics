from django.contrib import admin

from .models import TripSummary


@admin.register(TripSummary)
class TripSummaryAdmin(admin.ModelAdmin):
    list_display = ("delivery", "start_time", "end_time", "total_duration")

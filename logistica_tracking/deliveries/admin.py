from django.contrib import admin

from .models import Delivery, DeliveryAcceptAttempt


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "driver", "status", "created_at")
    list_filter = ("status",)


@admin.register(DeliveryAcceptAttempt)
class DeliveryAcceptAttemptAdmin(admin.ModelAdmin):
    list_display = ("delivery", "driver", "created_at")

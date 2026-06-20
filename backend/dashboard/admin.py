from django.contrib import admin

from .models import Alert, Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["recipient", "category", "title", "is_read", "created_at"]
    list_filter = ["category", "is_read"]


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ["alert_type", "reference_id", "severity", "status", "assigned_agent", "created_at"]
    list_filter = ["severity", "status"]

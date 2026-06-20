from django.contrib import admin

from .models import Dispute, DisputeEvidence, DisputeMessage


class DisputeMessageInline(admin.TabularInline):
    model = DisputeMessage
    extra = 0


class DisputeEvidenceInline(admin.TabularInline):
    model = DisputeEvidence
    extra = 0


@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    list_display = ["case_id", "title", "delivery", "status", "priority", "assigned_agent", "created_at"]
    list_filter = ["status", "priority"]
    search_fields = ["case_id", "title", "delivery__reference"]
    inlines = [DisputeMessageInline, DisputeEvidenceInline]

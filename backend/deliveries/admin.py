from django.contrib import admin

from .models import Bid, DeliveryRequest, Message, PriceProposal, StatusEvent, TrackingPing


class BidInline(admin.TabularInline):
    model = Bid
    extra = 0


class StatusEventInline(admin.TabularInline):
    model = StatusEvent
    extra = 0


@admin.register(DeliveryRequest)
class DeliveryRequestAdmin(admin.ModelAdmin):
    list_display = ["reference", "customer", "driver", "status", "target_price", "final_price", "created_at"]
    list_filter = ["status", "package_type", "service_type"]
    search_fields = ["reference", "customer__email", "driver__email"]
    inlines = [BidInline, StatusEventInline]


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ["delivery", "driver", "amount", "status", "created_at"]
    list_filter = ["status"]


@admin.register(TrackingPing)
class TrackingPingAdmin(admin.ModelAdmin):
    list_display = ["delivery", "lat", "lng", "recorded_at"]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["delivery", "sender", "created_at"]


@admin.register(PriceProposal)
class PriceProposalAdmin(admin.ModelAdmin):
    list_display = ["delivery", "proposed_by", "amount", "status", "created_at"]

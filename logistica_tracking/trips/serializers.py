from rest_framework import serializers

from .models import TripSummary


class TripSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = TripSummary
        fields = ["id", "delivery", "total_duration", "start_time", "end_time", "route_snapshot", "created_at"]

from django.utils import timezone

from deliveries.models import Delivery
from tracking.models import Location

from .models import TripSummary


def generate_trip_summary(delivery: Delivery) -> TripSummary:
    """
    Built from the reduced-interval Location rows (~60s apart) written
    during tracking, not the raw 5-10s pings which never reach Postgres.
    """
    locations = Location.objects.filter(delivery=delivery).order_by("timestamp")
    end_time = timezone.now()
    start_time = locations.first().timestamp if locations.exists() else end_time

    route_snapshot = [
        {"latitude": loc.latitude, "longitude": loc.longitude, "timestamp": loc.timestamp.isoformat()}
        for loc in locations
    ]

    summary, _ = TripSummary.objects.update_or_create(
        delivery=delivery,
        defaults={
            "total_duration": end_time - start_time,
            "start_time": start_time,
            "end_time": end_time,
            "route_snapshot": route_snapshot,
        },
    )
    return summary

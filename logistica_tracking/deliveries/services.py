import logging

from tracking.notify import notify_admins, notify_driver

from .models import Delivery, DeliveryAcceptAttempt

logger = logging.getLogger(__name__)


def assign_driver(delivery: Delivery, driver, *, resolved_by_admin: bool = False) -> Delivery:
    """Finalize a delivery's driver assignment and notify everyone involved."""
    other_driver_ids = list(
        DeliveryAcceptAttempt.objects.filter(delivery=delivery)
        .exclude(driver=driver)
        .values_list("driver_id", flat=True)
    )

    delivery.driver = driver
    delivery.status = Delivery.Status.ACCEPTED
    delivery.save(update_fields=["driver", "status", "updated_at"])
    DeliveryAcceptAttempt.objects.filter(delivery=delivery).delete()

    payload = {
        "delivery_id": delivery.id,
        "driver_id": driver.id,
        "resolved_by_admin": resolved_by_admin,
    }
    notify_driver(driver.id, "job_accepted", payload)
    for other_id in other_driver_ids:
        notify_driver(other_id, "job_taken", payload)
    notify_admins("job_taken", payload)
    logger.info(
        "Delivery %s: driver %s assigned%s", delivery.id, driver.id,
        " (resolved by admin)" if resolved_by_admin else "",
    )
    return delivery


def flag_conflict(delivery: Delivery):
    """Notify admins that two+ drivers accepted within the same window."""
    attempts = list(DeliveryAcceptAttempt.objects.filter(delivery=delivery).select_related("driver"))
    notify_admins(
        "conflict_alert",
        {
            "delivery_id": delivery.id,
            "driver_ids": [a.driver_id for a in attempts],
            "attempted_at": [a.created_at.isoformat() for a in attempts],
        },
    )
    logger.warning(
        "Delivery %s: accept conflict flagged among drivers %s",
        delivery.id, [a.driver_id for a in attempts],
    )
    return attempts

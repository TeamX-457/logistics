import logging

from celery import shared_task
from django.db import transaction

from .models import Delivery, DeliveryAcceptAttempt
from .services import assign_driver, flag_conflict

logger = logging.getLogger(__name__)


@shared_task
def resolve_accept_conflict(delivery_id):
    """
    Fires ACCEPT_CONFLICT_WINDOW_SECONDS after the first driver accept
    attempt for a delivery (scheduled from AcceptDeliveryView.post()).
    Locks the row, re-checks it's still unresolved, then finalizes: exactly
    one attempt in the window -> that driver is assigned; more than one ->
    admin is notified to resolve the conflict manually.

    Runs synchronously in-process locally/in tests (CELERY_TASK_ALWAYS_EAGER),
    or in a separate Celery worker process in production.
    """
    with transaction.atomic():
        try:
            delivery = Delivery.objects.select_for_update().get(pk=delivery_id)
        except Delivery.DoesNotExist:
            return

        if delivery.status != Delivery.Status.PENDING or delivery.driver_id:
            return

        attempts = list(DeliveryAcceptAttempt.objects.filter(delivery=delivery))
        if not attempts:
            return

        if len(attempts) == 1:
            assign_driver(delivery, attempts[0].driver)
            logger.info("Delivery %s assigned to driver %s", delivery.id, attempts[0].driver_id)
        else:
            flag_conflict(delivery)
            logger.warning(
                "Accept conflict on delivery %s: %d simultaneous attempts",
                delivery.id,
                len(attempts),
            )

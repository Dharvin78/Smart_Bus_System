from datetime import datetime, time
from django.utils import timezone

from apps.maintenance.models import Maintenance
from django.db import transaction
from django.db.models import Q



def is_maintenance_active(maintenance, now=None):
    """
    Maintenance is active only on its service date,
    after its scheduled start time has been reached.

    Only In Progress maintenance affects current status.
    """

    if maintenance.status != "In Progress":
        return False

    now = now or timezone.now()
    local_now = timezone.localtime(now)

    # Maintenance reserves only its service date.
    if local_now.date() != maintenance.service_date:
        return False

    # If no start time is provided, use midnight.
    start_time = maintenance.start_time or time.min

    return local_now.time().replace(
        tzinfo=None
    ) >= start_time

def vehicle_has_active_maintenance(vehicle, now=None):
    """
    Check whether a vehicle has active maintenance.
    """

    now = now or timezone.now()

    records = Maintenance.objects.filter(
        vehicle=vehicle,
        status="In Progress",
    )

    return any(
        is_maintenance_active(record, now)
        for record in records
    )


def driver_has_active_maintenance(driver, now=None):
    """
    Check whether a driver has active maintenance duty.
    """

    now = now or timezone.now()

    records = Maintenance.objects.filter(
        assigned_driver=driver,
        status="In Progress",
    )

    return any(
        is_maintenance_active(record, now)
        for record in records
    )


def activate_scheduled_maintenance(now=None):
    """
    Activate scheduled maintenance when its start
    date and optional start time have been reached.

    Completed and Cancelled records are not changed.
    """

    now = now or timezone.now()
    local_now = timezone.localtime(now)

    today = local_now.date()
    current_time = local_now.time()

    with transaction.atomic():

        records = Maintenance.objects.filter(
            status="Scheduled"
        ).filter(
            Q(service_date__lt=today) |
            Q(
                service_date=today,
                start_time__isnull=True,
            ) |
            Q(
                service_date=today,
                start_time__lte=current_time,
            )
        )

        updated_count = records.update(
            status="In Progress",
            updated_at=now,
        )

    return updated_count
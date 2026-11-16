
from datetime import datetime

from django.db.models import Q
from django.utils import timezone

from apps.bookings.models import Booking
from apps.maintenance.models import Maintenance
from apps.maintenance.services import (
    activate_scheduled_maintenance,
    vehicle_has_active_maintenance,
    driver_has_active_maintenance,
)


# ============================================================
# 1. TRIP ACTIVITY DETECTION
# ============================================================

def is_trip_active(booking, now=None):
    """
    Determine whether a confirmed booking is currently active.

    A trip starts at its scheduled departure time and
    reserves the vehicle and driver through the entire
    return date.
    """

    if booking.booking_status != "Confirmed":
        return False

    now = now or timezone.now()
    local_now = timezone.localtime(now)

    departure = timezone.make_aware(
        datetime.combine(
            booking.travel_date,
            booking.departure_time,
        ),
        timezone.get_current_timezone(),
    )

    # Trip has not started.
    if now < departure:
        return False

    # Use travel date if return date is not provided.
    return_date = booking.return_date or booking.travel_date

    # Trip is no longer active after the return date.
    if local_now.date() > return_date:
        return False

    return True


def vehicle_has_active_trip(vehicle, now=None):
    """
    Check whether the vehicle is currently on a trip.
    """

    now = now or timezone.now()

    bookings = Booking.objects.filter(
        vehicle=vehicle,
        booking_status="Confirmed",
    )

    return any(
        is_trip_active(booking, now)
        for booking in bookings
    )


def driver_has_active_trip(driver, now=None):
    """
    Check whether the driver is currently on a trip.
    """

    now = now or timezone.now()

    bookings = Booking.objects.filter(
        driver=driver,
        booking_status="Confirmed",
    )

    return any(
        is_trip_active(booking, now)
        for booking in bookings
    )


# ============================================================
# 2. CURRENT VEHICLE AND DRIVER STATUS
# ============================================================

def get_vehicle_current_status(vehicle, now=None):
    """
    Calculate the vehicle's effective current status.

    Priority:
    1. Inactive
    2. Maintenance
    3. Booked
    4. Available
    """

    now = now or timezone.now()

    # Activate maintenance whose scheduled start has arrived.
    activate_scheduled_maintenance(now)

    # Preserve manual restriction.
    if vehicle.status == "Inactive":
        return "Inactive"

    # Check active maintenance.
    if vehicle_has_active_maintenance(vehicle, now):
        return "Maintenance"

    # Check active trip.
    if vehicle_has_active_trip(vehicle, now):
        return "Booked"

    return "Available"


def get_driver_current_status(driver, now=None):
    """
    Calculate the driver's effective current status.

    Priority:
    1. Leave / Inactive
    2. On Duty
    3. On Trip
    4. Available
    """

    now = now or timezone.now()

    # Activate maintenance whose scheduled start has arrived.
    activate_scheduled_maintenance(now)

    # Preserve manual restrictions.
    if driver.status in ("Leave", "Inactive"):
        return driver.status

    # Check active maintenance assignment.
    if driver_has_active_maintenance(driver, now):
        return "On Duty"

    # Check active trip.
    if driver_has_active_trip(driver, now):
        return "On Trip"

    return "Available"


# ============================================================
# 3. BOOKING DATE CONFLICT DETECTION
# ============================================================

def has_booking_date_conflict(
    travel_date,
    return_date,
    vehicle=None,
    driver=None,
    exclude_booking_id=None,
):
    """
    Check whether a vehicle or driver has an overlapping
    confirmed booking.

    The entire return date is reserved.
    """

    if vehicle is None and driver is None:
        raise ValueError(
            "A vehicle or driver must be provided."
        )

    if return_date is None:
        return_date = travel_date

    if return_date < travel_date:
        raise ValueError(
            "Return date cannot be before travel date."
        )

    bookings = Booking.objects.filter(
        booking_status="Confirmed",
        travel_date__lte=return_date,
    ).filter(
        Q(return_date__gte=travel_date) |
        Q(
            return_date__isnull=True,
            travel_date__gte=travel_date,
        )
    )

    # Exclude the current booking when necessary.
    if exclude_booking_id is not None:
        bookings = bookings.exclude(
            pk=exclude_booking_id
        )

    # Check vehicle assignment.
    if vehicle is not None:
        bookings = bookings.filter(
            vehicle=vehicle
        )

    # Check driver assignment.
    if driver is not None:
        bookings = bookings.filter(
            driver=driver
        )

    return bookings.exists()


# ============================================================
# 4. MAINTENANCE DATE CONFLICT DETECTION
# ============================================================

def has_maintenance_date_conflict(
    travel_date,
    return_date,
    vehicle=None,
    driver=None,
):
    """
    Check whether a vehicle or driver has maintenance
    during the requested booking dates.

    Maintenance reserves its entire service date only.
    """

    if vehicle is None and driver is None:
        raise ValueError(
            "A vehicle or driver must be provided."
        )

    if return_date is None:
        return_date = travel_date

    if return_date < travel_date:
        raise ValueError(
            "Return date cannot be before travel date."
        )

    maintenance_records = Maintenance.objects.filter(
        status__in=["Scheduled", "In Progress"],
        service_date__gte=travel_date,
        service_date__lte=return_date,
    )

    # Check vehicle maintenance.
    if vehicle is not None:
        maintenance_records = maintenance_records.filter(
            vehicle=vehicle
        )

    # Check driver maintenance assignment.
    if driver is not None:
        maintenance_records = maintenance_records.filter(
            assigned_driver=driver
        )

    return maintenance_records.exists()

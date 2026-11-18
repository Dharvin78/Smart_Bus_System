from datetime import datetime, timedelta

from django.db.models import Q
from django.utils import timezone

from apps.bookings.models import Booking
from apps.maintenance.models import Maintenance
from apps.maintenance.services import (
    activate_scheduled_maintenance,
    vehicle_has_active_maintenance,
    driver_has_active_maintenance,
)
from django.db import transaction
from django.db.models import Exists, OuterRef
from apps.payments.models import Payment
from apps.audit.models import AuditLog


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


# ============================================================
# 5. DRIVER REST RECOMMENDATION
# ============================================================

def get_driver_rest_recommendation(
    driver,
    travel_date,
    exclude_booking_id=None,
):
    """
    Recommend one rest day after a driver has been
    assigned a trip lasting 3 or more calendar days.

    This is a recommendation only.
    It does not block booking approval.
    """

    previous_date = travel_date - timedelta(days=1)

    previous_bookings = Booking.objects.filter(
        driver=driver,
        booking_status__in=["Confirmed", "Completed"],
        travel_date__lte=previous_date,
    ).filter(
        Q(return_date=previous_date) |
        Q(
            return_date__isnull=True,
            travel_date=previous_date,
        )
    )

    if exclude_booking_id is not None:
        previous_bookings = previous_bookings.exclude(
            pk=exclude_booking_id
        )

    for booking in previous_bookings:

        trip_end = booking.return_date or booking.travel_date

        trip_duration = (
            trip_end - booking.travel_date
        ).days + 1

        if trip_duration >= 3:
            return (
                f"Rest Recommended: {driver.full_name} "
                f"has a {trip_duration}-day trip ending "
                f"on {trip_end:%d %B %Y}. "
                f"Consider allowing one rest day on "
                f"{travel_date:%d %B %Y} before assigning "
                f"another trip."
            )

    return None

# ============================================================
# 6. AUTOMATIC EXPIRATION OF PENDING BOOKINGS
# ============================================================

def expire_pending_bookings():
    """
    Automatically cancel pending bookings when their
    scheduled departure date and time have passed.

    Returns the number of expired bookings.
    """

    now = timezone.localtime()
    today = now.date()
    current_time = now.time()

    expired_bookings = Booking.objects.filter(
        booking_status="Pending"
    ).filter(
        Q(travel_date__lt=today) |
        Q(
            travel_date=today,
            departure_time__lte=current_time,
        )
    )

    return expired_bookings.update(
        booking_status="Cancelled",
        rejection_reason=(
            "Automatically cancelled because the scheduled "
            "departure time passed without approval."
        ),
        cancelled_at=timezone.now(),
        updated_at=timezone.now(),
    )


# ============================================================
# 7. AUTOMATIC EXPIRATION OF UNPAID CONFIRMED BOOKINGS
# ============================================================

def expire_unpaid_confirmed_bookings(dry_run=True):
    """
    Cancel unpaid confirmed bookings when:

    1. Their payment deadline has expired.
    2. No payment deadline exists and departure has passed.

    Protect bookings with Paid or Partially Paid records.

    dry_run=True:
        Identify bookings without modifying records.

    dry_run=False:
        Cancel eligible bookings and pending payments.
    """

    now = timezone.now()
    local_now = timezone.localtime(now)

    paid_payments = Payment.objects.filter(
        booking_id=OuterRef("pk"),
        payment_status__in=["Paid", "Partially Paid"],
    )

    candidates = Booking.objects.filter(
        booking_status="Confirmed",
        payment_status="Pending",
    ).annotate(
        has_successful_payment=Exists(paid_payments)
    ).filter(
        has_successful_payment=False
    ).filter(
        Q(
            payment_deadline__isnull=False,
            payment_deadline__lte=now,
        )
        |
        Q(
            payment_deadline__isnull=True,
            travel_date__lt=local_now.date(),
        )
        |
        Q(
            payment_deadline__isnull=True,
            travel_date=local_now.date(),
            departure_time__lte=local_now.time(),
        )
    )

    if dry_run:
        return list(
            candidates.values_list(
                "booking_number",
                flat=True,
            )
        )

    cancelled = []

    with transaction.atomic():

        # Acquire a SQLite write lock before checking
        # and updating booking/payment records.
        Booking.objects.filter(
            pk__in=candidates.values("pk")
        ).update(
            updated_at=now
        )

        # Re-evaluate after acquiring the write lock.
        for booking in candidates:

            if booking.payment_deadline is not None:
                expired = now >= booking.payment_deadline
            else:
                expired = now >= booking.departure_datetime

            if not expired:
                continue

            # Recheck payment records before cancellation.
            if Payment.objects.filter(
                booking=booking,
                payment_status__in=["Paid", "Partially Paid"],
            ).exists():
                continue

            if booking.booking_status != "Confirmed":
                continue

            booking.booking_status = "Cancelled"
            booking.cancelled_at = now
            booking.rejection_reason = (
                "Automatically cancelled because payment "
                "was not completed before the deadline."
                if booking.payment_deadline is not None
                else
                "Automatically cancelled because the "
                "scheduled departure passed without payment."
            )

            booking.save(
                update_fields=[
                    "booking_status",
                    "cancelled_at",
                    "rejection_reason",
                    "updated_at",
                ]
            )

            
            Payment.objects.filter(
                booking=booking,
                payment_status="Pending",
            ).update(
                payment_status="Cancelled",
            )

            # Record automatic cancellation in the audit log.
            
            AuditLog.objects.create(
                user=None,
                module="Bookings",
                action="PAYMENT_EXPIRED",
                booking=booking,
                customer=booking.customer,
                description=(
                    f"Booking {booking.booking_number} was automatically "
                    f"cancelled by the system due to an expired payment "
                    f"deadline or an unpaid departure. "
                    f"Reason: {booking.rejection_reason}"
                ),
                ip_address=None,
            )


            cancelled.append(booking.booking_number)

    return cancelled
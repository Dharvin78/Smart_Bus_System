
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from django.utils import timezone


def calculate_cancellation_refund(booking, paid_amount):
    """
    Calculate cancellation charges and refunds.

    Cancellation is prohibited within 4 hours
    of the scheduled departure time.
    """

    departure = timezone.make_aware(
        datetime.combine(
            booking.travel_date,
            booking.departure_time,
        ),
        timezone.get_current_timezone(),
    )

    now = timezone.now()

    hours_remaining = (
        departure - now
    ).total_seconds() / 3600

    # Cancellation must be at least 4 hours
    # before scheduled departure.
    if hours_remaining < 4:
        raise ValueError(
            "Booking cancellation is not allowed "
            "within 4 hours of departure."
        )

    if hours_remaining >= 168:
        charge_percentage = Decimal("0")

    elif hours_remaining >= 48:
        charge_percentage = Decimal("20")

    elif hours_remaining >= 24:
        charge_percentage = Decimal("30")

    else:
        charge_percentage = Decimal("35")

    paid_amount = Decimal(str(paid_amount))

    if not paid_amount.is_finite() or paid_amount < 0:
        raise ValueError("Invalid payment amount.")

    cancellation_charge = (
        paid_amount * charge_percentage / Decimal("100")
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    refund_amount = paid_amount - cancellation_charge

    return {
        "charge_percentage": charge_percentage,
        "cancellation_charge": cancellation_charge,
        "refund_amount": refund_amount,
        "restore_loyalty_points": charge_percentage == 0,
    }

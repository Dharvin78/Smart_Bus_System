from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone

from apps.bookings.models import Booking


def complete_expired_bookings():
    """
    Automatically complete confirmed bookings when
    their scheduled trip date has passed.

    If return_date exists, use return_date.
    Otherwise, use travel_date.

    Only confirmed bookings are updated.
    """

    today = timezone.localdate()

    eligible_bookings = Booking.objects.filter(
        booking_status="Confirmed"
    ).filter(
        Q(return_date__lt=today)
        | Q(
            return_date__isnull=True,
            travel_date__lt=today
        )
    )

    with transaction.atomic():
        completed_count = eligible_bookings.update(
            booking_status="Completed",
            updated_at=timezone.now()
        )

    return completed_count

from django.db import transaction
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone

from apps.bookings.models import Booking
from apps.loyalty.models import LoyaltyTransaction
from apps.loyalty.services import RM_PER_POINT, award_loyalty_points


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

        # Include eligible trips completed before loyalty was enabled.
        earnings = LoyaltyTransaction.objects.filter(
            booking_id=OuterRef("pk"), transaction_type="Earned",
        )
        uncredited_bookings = Booking.objects.filter(
            booking_status="Completed", payment_status="Paid",
            total_price__gte=RM_PER_POINT,
        ).filter(~Exists(earnings)).order_by("customer_id", "pk")
        for booking in uncredited_bookings:
            award_loyalty_points(booking, earned_at=booking.updated_at)

    return completed_count

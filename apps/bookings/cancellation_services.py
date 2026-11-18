
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.audit.models import AuditLog
from apps.loyalty.models import LoyaltyTransaction
from apps.loyalty.services import restore_redeemed_points

from .models import Booking


def calculate_cancellation_refund(booking, paid_amount, *, now=None):
    """
    Calculate cancellation charges and refunds.

    Cancellation is prohibited within 4 hours
    of the scheduled departure time.
    """

    now = now or timezone.now()

    hours_remaining = (
        booking.departure_datetime - now
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
        "restore_loyalty_points": hours_remaining >= 48,
    }


def cancellation_quote(booking, *, now=None):
    if booking.booking_status not in {"Pending", "Confirmed"}:
        raise ValueError("This booking can no longer be cancelled.")

    payments = list(booking.payments.filter(
        payment_status__in=["Paid", "Partially Paid"],
    ).order_by("pk"))
    paid_amount = sum((payment.amount for payment in payments), Decimal("0.00"))
    if booking.payment_status == "Paid" and not payments:
        raise ValueError("The payment record is missing. Please contact staff to cancel.")

    if booking.booking_status == "Pending" and not payments:
        return {
            "payments": [], "paid_amount": paid_amount, "charge_percentage": Decimal("0"),
            "cancellation_charge": paid_amount, "refund_amount": paid_amount,
            "redemption": None, "points_used": 0, "points_returned": 0,
        }

    quote = calculate_cancellation_refund(booking, paid_amount, now=now)
    redemption = LoyaltyTransaction.objects.filter(
        booking=booking, transaction_type="Redeemed", points__lt=0,
    ).first()
    points_used = -redemption.points if redemption else 0
    return {
        **quote,
        "payments": payments,
        "paid_amount": paid_amount,
        "redemption": redemption,
        "points_used": points_used,
        "points_returned": points_used if quote["restore_loyalty_points"] else 0,
    }


@transaction.atomic
def cancel_customer_booking(booking_id, customer, user, ip_address, *, expected_quote=None):
    # Serialize with payment, approval, reward redemption, and automatic cancellation.
    Booking.objects.filter(pk=booking_id, customer=customer).update(updated_at=F("updated_at"))
    booking = get_object_or_404(Booking, pk=booking_id, customer=customer)
    now = timezone.now()
    quote = cancellation_quote(booking, now=now)
    if booking.booking_status == "Confirmed" and expected_quote != cancellation_quote_key(quote):
        raise ValueError("Review the current refund and points before confirming cancellation.")

    booking.booking_status = "Cancelled"
    booking.cancelled_at = now
    booking.cancellation_charge_percentage = quote["charge_percentage"]
    booking.cancellation_charge = quote["cancellation_charge"]
    booking.refund_amount = quote["refund_amount"]
    booking.refund_status = "Pending" if booking.refund_amount else "Not Required"
    booking.save(update_fields=[
        "booking_status", "cancelled_at", "cancellation_charge_percentage",
        "cancellation_charge", "refund_amount", "refund_status", "updated_at",
    ])
    remaining_refund = booking.refund_amount
    for payment in quote["payments"]:
        payment.refund_amount = min(payment.amount, remaining_refund)
        payment.save(update_fields=["refund_amount", "updated_at"])
        remaining_refund -= payment.refund_amount
    booking.payments.filter(payment_status="Pending").update(payment_status="Cancelled")

    if quote["points_returned"]:
        quote["points_returned"] = restore_redeemed_points(booking, quote["redemption"], now)

    AuditLog.objects.create(
        user=user,
        module="Booking",
        action="CANCEL",
        booking=booking,
        customer=customer,
        description=(
            f"Customer cancelled {booking.booking_number}. "
            f"Cancellation charge: RM {booking.cancellation_charge:.2f}. "
            f"Refund due: RM {booking.refund_amount:.2f}. "
            f"Points restored: {quote['points_returned']} of {quote['points_used']}."
        ),
        ip_address=ip_address,
    )
    return booking, quote


def cancellation_quote_key(quote):
    return "|".join((
        f"{quote['paid_amount']:.2f}",
        f"{quote['refund_amount']:.2f}",
        str(quote["points_used"]),
        str(quote["points_returned"]),
    ))

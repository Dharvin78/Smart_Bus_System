import uuid

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.bookings.models import Booking
from .models import Payment


class PaymentProcessingError(Exception):
    pass


def process_simulated_payment(booking, customer, payment_method):
    try:
        with transaction.atomic():
            locked_booking = Booking.objects.select_for_update().get(
                pk=booking.pk,
                customer=customer,
            )

            if locked_booking.booking_status != "Confirmed":
                raise PaymentProcessingError(
                    "This booking is not available for payment."
                )

            if (
                locked_booking.payment_status == "Paid"
                or Payment.objects.filter(
                    booking=locked_booking,
                    payment_status="Paid",
                ).exists()
            ):
                raise PaymentProcessingError(
                    "This booking has already been paid."
                )

            if (
                locked_booking.total_price is None
                or locked_booking.total_price <= 0
            ):
                raise PaymentProcessingError(
                    "This booking has an invalid payment amount."
                )

            payment = (
                Payment.objects.filter(
                    booking=locked_booking,
                    payment_status="Pending",
                )
                .order_by("-created_at", "-pk")
                .first()
            )

            if payment is None:
                payment = Payment(booking=locked_booking)

            payment.amount = locked_booking.total_price
            payment.payment_method = payment_method
            payment.payment_status = "Paid"
            payment.payment_date = timezone.localdate()
            payment.transaction_id = (
                f"SIM-{timezone.localdate():%Y%m%d}-"
                f"{uuid.uuid4().hex[:8].upper()}"
            )
            payment.save()

            locked_booking.payment_status = "Paid"
            locked_booking.save(update_fields=["payment_status"])

            return payment

    except IntegrityError as exc:
        raise PaymentProcessingError(
            "This booking has already been paid or the payment could not be completed."
        ) from exc
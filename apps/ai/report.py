from apps.bookings.models import Booking
from apps.payments.models import Payment

from django.db.models import Sum

from .services import predict_next_month


def generate_business_report():

    total_bookings = Booking.objects.count()

    completed = Booking.objects.filter(
        booking_status="Completed"
    ).count()

    pending = Booking.objects.filter(
        booking_status="Pending"
    ).count()

    cancelled = Booking.objects.filter(
        booking_status="Cancelled"
    ).count()

    revenue = (
        Payment.objects.filter(
            payment_status="Paid"
        ).aggregate(
            total=Sum("amount")
        )["total"] or 0
    )

    prediction = predict_next_month()

    report = []

    report.append(
        f"The company currently has {total_bookings} bookings."
    )

    report.append(
        f"{completed} bookings have been completed successfully."
    )

    report.append(
        f"{pending} bookings are waiting for confirmation."
    )

    report.append(
        f"{cancelled} bookings have been cancelled."
    )

    report.append(
        f"Total recorded revenue is RM {revenue:,.2f}."
    )

    if prediction:

        report.append(
            f"The AI predicts next month's revenue to be approximately RM {prediction:,.2f}."
        )

    else:

        report.append(
            "The AI model needs more historical payment data before a revenue forecast can be generated."
        )

    return report
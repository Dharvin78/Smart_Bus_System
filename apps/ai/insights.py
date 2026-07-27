from apps.bookings.models import Booking
from apps.payments.models import Payment


def generate_ai_insights(prediction=None):

    insights = []

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

    paid = Payment.objects.filter(
        payment_status="Paid"
    ).count()

    if total_bookings > 0:

        completion_rate = (completed / total_bookings) * 100

        if completion_rate >= 80:

            insights.append({
                "type": "success",
                "icon": "fa-circle-check",
                "title": "Excellent Completion Rate",
                "message": f"{completion_rate:.1f}% of bookings have been completed."
            })

    if pending > 5:

        insights.append({
            "type": "warning",
            "icon": "fa-clock",
            "title": "Pending Bookings",
            "message": f"{pending} bookings are waiting for confirmation."
        })

    if cancelled > 3:

        insights.append({
            "type": "danger",
            "icon": "fa-circle-xmark",
            "title": "High Cancellation Rate",
            "message": f"{cancelled} bookings have been cancelled."
        })

    if prediction:

        insights.append({
            "type": "info",
            "icon": "fa-chart-line",
            "title": "Revenue Forecast",
            "message": f"Predicted revenue next month is RM {prediction:,.2f}."
        })

    if paid >= 10:

        insights.append({
            "type": "primary",
            "icon": "fa-brain",
            "title": "AI Model Status",
            "message": "The machine learning model has enough historical payment data for forecasting."
        })

    return insights
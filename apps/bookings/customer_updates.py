import logging

from django.utils import timezone

from apps.emails.services import send_booking_update_email
from apps.notifications.services import notify_customer

logger = logging.getLogger(__name__)


def send_customer_booking_update(booking, event, bookings_url, *, cancellation=None):
    reference = booking.booking_number
    details = []
    if event == "submitted":
        title, notification_type = "Booking Request Received", "info"
        message = f"We received your booking request {reference}. It is awaiting staff review."
    elif event == "approved":
        title, notification_type = "Booking Approved", "success"
        deadline = timezone.localtime(booking.payment_deadline)
        message = (
            f"Your booking {reference} was approved. Pay RM {booking.total_price:,.2f} "
            f"by {deadline:%d %b %Y, %I:%M %p %Z} to secure your trip."
        )
    elif event == "rejected":
        title, notification_type = "Booking Rejected", "warning"
        message = f"Your booking request {reference} was rejected."
        if booking.rejection_reason:
            details.append(("Reason", booking.rejection_reason))
    elif event == "cancelled":
        title, notification_type = "Booking Cancelled", "info"
        message = f"Your booking {reference} has been cancelled."
        if cancellation["refund_amount"]:
            message += (
                f" RM {cancellation['refund_amount']:,.2f} will be refunded "
                "within 7 working days."
            )
        else:
            message += " No money is due for refund."
        details.extend([
            ("Amount paid", f"RM {cancellation['paid_amount']:,.2f}"),
            ("Cancellation charge", f"RM {cancellation['cancellation_charge']:,.2f}"),
            ("Refund amount", f"RM {cancellation['refund_amount']:,.2f}"),
            ("Loyalty points used", cancellation["points_used"]),
            ("Loyalty points returned", cancellation["points_returned"]),
            ("Loyalty points not returned", cancellation["points_used"] - cancellation["points_returned"]),
        ])
    else:
        raise ValueError(f"Unsupported booking update: {event}")

    notification_message = message
    if event == "rejected" and details:
        notification_message = f"{message} Reason: {booking.rejection_reason}"
    elif event == "cancelled":
        notification_message += (
            f" Loyalty points returned: {cancellation['points_returned']} "
            f"of {cancellation['points_used']} used."
        )

    try:
        notify_customer(booking, title, notification_message, notification_type)
    except Exception:
        logger.exception("Could not create %s notification for %s", event, reference)

    try:
        send_booking_update_email(booking, title, message, details, bookings_url)
    except Exception:
        logger.exception("Could not send %s email for %s", event, reference)

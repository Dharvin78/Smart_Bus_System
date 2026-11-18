from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import formats


def send_booking_confirmation(booking):

    html = render_to_string(
        "emails/booking_confirmation.html",
        {
            "customer_name": f"{booking.customer.first_name} {booking.customer.last_name}",
            "booking_number": booking.booking_number,
            "travel_date": booking.travel_date,
            "departure_time": booking.departure_time,
            "pickup_location": booking.pickup_location,
            "destination": booking.destination,
            "vehicle": booking.vehicle,
            "driver": booking.driver,
            "passenger_count": booking.passenger_count,
            "total_price": booking.total_price,
            "booking_status": booking.booking_status,
        }
    )

    email = EmailMultiAlternatives(
        subject="Booking Confirmation - Smart Bus Charter System",
        body="",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[booking.customer.email],
    )

    email.attach_alternative(html, "text/html")
    email.send()

def send_payment_receipt(payment):

    booking = payment.booking

    html = render_to_string(
        "emails/payment_receipt.html",
        {
            "customer_name": f"{booking.customer.first_name} {booking.customer.last_name}",
            "payment_id": payment.id,
            "transaction_id": payment.transaction_id,
            "booking_number": booking.booking_number,
            "payment_date": payment.payment_date,
            "payment_method": payment.payment_method,
            "amount": payment.amount,
            "payment_status": payment.payment_status,
        }
    )

    email = EmailMultiAlternatives(
        subject="Payment Receipt - Smart Bus Charter System",
        body="",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[booking.customer.email],
    )

    email.attach_alternative(html, "text/html")
    email.send()



def send_booking_update_email(booking, title, message, details, bookings_url):
    customer = booking.customer
    recipient = customer.email or getattr(customer.user, "email", "")
    if not recipient:
        return False

    customer_name = f"{customer.first_name} {customer.last_name}".strip() or "there"
    trip_details = [
        ("Booking reference", booking.booking_number),
        ("Travel date", formats.date_format(booking.travel_date, "j M Y")),
        ("Departure time", formats.time_format(booking.departure_time, "g:i A")),
        ("Pickup", booking.pickup_location),
        ("Destination", booking.destination),
        *details,
    ]
    html = render_to_string("emails/booking_update.html", {
        "title": title,
        "customer_name": customer_name,
        "message": message,
        "trip_details": trip_details,
        "bookings_url": bookings_url,
    })
    body = "\n".join([
        f"Hi {customer_name},", "", message, "",
        *(f"{label}: {value}" for label, value in trip_details),
        "", f"My Bookings: {bookings_url}",
    ])

    email = EmailMultiAlternatives(
        subject=f"{title} - {booking.booking_number}",
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient],
    )
    email.attach_alternative(html, "text/html")
    return email.send() == 1

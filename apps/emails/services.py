from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


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
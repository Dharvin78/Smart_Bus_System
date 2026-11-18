from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import UserProfile
from apps.bookings.models import Booking
from apps.customers.models import Customer


class CustomerPaymentCountdownTests(TestCase):
    def test_dashboard_shows_deadlines_for_confirmed_unpaid_bookings(self):
        user = get_user_model().objects.create_user(username="countdown-customer")
        UserProfile.objects.update_or_create(user=user, defaults={"role": "Customer"})
        customer = Customer.objects.create(user=user, first_name="Customer")
        self.client.force_login(user)
        now = timezone.now()
        departure = timezone.localtime(now + timedelta(days=2))
        trip = {
            "customer": customer, "pickup_location": "Airport", "destination": "City",
            "travel_date": departure.date(), "departure_time": departure.time(),
            "passenger_count": 10, "booking_status": "Confirmed", "total_price": 100,
        }
        active = Booking.objects.create(**trip, payment_deadline=now + timedelta(minutes=30))
        expired = Booking.objects.create(**trip, payment_deadline=now - timedelta(minutes=30))
        legacy = Booking.objects.create(**trip)
        Booking.objects.create(**trip, payment_status="Paid", payment_deadline=active.payment_deadline)

        response = self.client.get(reverse("customer_dashboard"))
        self.assertContains(response, "payment_countdown.js")
        self.assertContains(response, 'data-payment-deadline=', count=3)
        self.assertContains(response, "Payment deadline passed")
        self.assertContains(response, 'btn btn-success d-none" data-pay-now', count=1)
        self.assertEqual(
            [booking.pk for booking in response.context["awaiting_payment"]],
            [active.pk, legacy.pk, expired.pk],
        )

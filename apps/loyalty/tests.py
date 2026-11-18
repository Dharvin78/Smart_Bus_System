from datetime import time, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import UserProfile
from apps.bookings.auto_completion_services import complete_expired_bookings
from apps.bookings.models import Booking
from apps.customers.models import Customer
from apps.payments.models import Payment

from .models import LoyaltyReward
from .services import award_loyalty_points


class LoyaltyFlowTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username="loyalty-customer")
        UserProfile.objects.update_or_create(user=user, defaults={"role": "Customer"})
        self.customer = Customer.objects.create(user=user, first_name="Loyalty")
        self.client.force_login(user)
        self.dashboard = reverse("loyalty:dashboard")

    def make_booking(self, **overrides):
        fields = {
            "customer": self.customer,
            "pickup_location": "Airport",
            "destination": "City Centre",
            "travel_date": timezone.localdate() + timedelta(days=2),
            "departure_time": time(9),
            "passenger_count": 10,
            "total_price": Decimal("6000.00"),
            "booking_status": "Confirmed",
        }
        return Booking.objects.create(**(fields | overrides))

    def test_completion_awards_paid_booking_once_and_shows_tier(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        paid = self.make_booking(travel_date=yesterday, payment_status="Paid")
        self.make_booking(travel_date=yesterday)
        historical = self.make_booking(
            travel_date=yesterday, booking_status="Completed", payment_status="Paid",
            total_price=Decimal("100.00"),
        )
        self.assertEqual(complete_expired_bookings(), 2)
        self.assertEqual(complete_expired_bookings(), 0)

        account = self.customer.loyalty_account
        self.assertEqual(account.points_balance, 610)
        self.assertEqual(account.membership_tier, "Silver")
        self.assertEqual(account.transactions.count(), 2)
        response = self.client.get(self.dashboard)
        self.assertContains(response, paid.booking_number)
        self.assertContains(response, historical.booking_number)
        self.assertContains(response, "Silver")

    def test_checkout_redeems_once_and_charges_discounted_price(self):
        earning_booking = self.make_booking(booking_status="Completed", payment_status="Paid")
        award_loyalty_points(earning_booking)
        booking = self.make_booking()
        payment = Payment.objects.create(
            booking=booking, amount=booking.total_price, payment_date=timezone.localdate(),
        )
        reward = LoyaltyReward.objects.create(
            name="Charter discount", points_required=200, discount_percentage=10,
            max_discount=Decimal("50.00"),
        )
        redeem_url = reverse("loyalty:redeem", args=[booking.pk])
        payment_url = reverse("payments:payment_create")
        checkout = f"{payment_url}?booking={booking.pk}"

        self.assertContains(self.client.get(checkout), reward.name)
        self.assertRedirects(self.client.post(redeem_url, {"reward_id": reward.pk}), checkout)
        self.assertContains(self.client.get(checkout), "Loyalty discount")
        self.client.post(redeem_url, {"reward_id": reward.pk})
        account = self.customer.loyalty_account
        account.refresh_from_db()
        self.assertEqual(account.points_balance, 400)

        booking.refresh_from_db()
        payment.refresh_from_db()
        self.assertEqual(booking.original_price, Decimal("6000.00"))
        self.assertEqual(booking.total_price, Decimal("5950.00"))
        self.assertEqual(payment.amount, booking.total_price)
        with patch("apps.payments.views.send_payment_receipt"):
            response = self.client.post(payment_url, {
                "booking_id": booking.pk,
                "payment_method": "Credit Card",
                "simulation_result": "success",
            })
        self.assertEqual(response.status_code, 302)
        payment.refresh_from_db()
        self.assertEqual(payment.payment_status, "Paid")
        self.assertEqual(payment.amount, Decimal("5950.00"))

    def test_expiry_and_booking_ownership(self):
        old_booking = self.make_booking(booking_status="Completed", payment_status="Paid")
        award_loyalty_points(old_booking, earned_at=timezone.now() - timedelta(days=200))
        self.assertContains(self.client.get(self.dashboard), "Expired")
        self.client.get(self.dashboard)
        account = self.customer.loyalty_account
        account.refresh_from_db()
        self.assertEqual(account.points_balance, 0)
        self.assertEqual(account.lifetime_points, 600)
        self.assertEqual(account.transactions.filter(transaction_type="Expired").count(), 1)

        stranger = Customer.objects.create(first_name="Other customer")
        booking = self.make_booking(customer=stranger)
        redeem_url = reverse("loyalty:redeem", args=[booking.pk])
        self.assertEqual(self.client.get(redeem_url).status_code, 405)
        self.assertEqual(self.client.post(redeem_url, {"reward_id": 1}).status_code, 404)

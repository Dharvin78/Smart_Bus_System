from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import UserProfile
from apps.customers.models import Customer
from apps.loyalty.models import LoyaltyAccount, LoyaltyTransaction
from apps.payments.admin import PaymentAdmin
from apps.payments.models import Payment

from .cancellation_services import calculate_cancellation_refund
from .models import Booking


class BookingCancellationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="cancelling-customer", email="customer@example.com",
        )
        UserProfile.objects.update_or_create(user=self.user, defaults={"role": "Customer"})
        self.customer = Customer.objects.create(user=self.user, first_name="Customer")
        self.account = LoyaltyAccount.objects.create(customer=self.customer, lifetime_points=100)
        self.client.force_login(self.user)

    def make_booking(self, hours):
        departure = timezone.localtime() + timedelta(hours=hours)
        booking = Booking.objects.create(
            customer=self.customer, pickup_location="Airport", destination="City",
            travel_date=departure.date(), departure_time=departure.time(),
            passenger_count=10, total_price=Decimal("900.00"),
            booking_status="Confirmed", payment_status="Paid",
        )
        payment = Payment.objects.create(
            booking=booking, amount=booking.total_price,
            payment_status="Paid", payment_date=timezone.localdate(),
        )
        LoyaltyTransaction.objects.create(
            booking=booking, account=self.account, transaction_type="Redeemed", points=-100,
        )
        return booking, payment, reverse("bookings:customer_cancel_booking", args=[booking.pk])

    def cancel(self, url, quote):
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(url, {"quote": quote})

    def test_under_48_hours_refunds_money_without_returning_points(self):
        booking, payment, url = self.make_booking(30)
        preview = self.client.get(url)
        self.assertContains(preview, "630.00")
        self.assertContains(preview, "less than 48 hours")
        response = self.cancel(url, preview.context["quote_key"])
        self.assertRedirects(response, reverse("bookings:customer_bookings"))
        self.cancel(url, preview.context["quote_key"])

        booking.refresh_from_db()
        payment.refresh_from_db()
        self.account.refresh_from_db()
        self.assertEqual(booking.booking_status, "Cancelled")
        self.assertEqual(booking.refund_status, "Pending")
        self.assertEqual(payment.refund_amount, Decimal("630.00"))
        self.assertEqual(self.account.points_balance, 0)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn("RM 630.00 will be refunded within 7 working days", email.body)
        self.assertIn("Loyalty points not returned: 100", email.body)
        self.assertIn("630.00", email.alternatives[0].content)
        self.assertContains(self.client.get(reverse("bookings:customer_bookings")), "630.00")

    def test_at_least_48_hours_returns_points_and_supports_recording_refund(self):
        booking, payment, url = self.make_booking(60)
        at_boundary = booking.departure_datetime - timedelta(hours=48)
        self.assertTrue(calculate_cancellation_refund(
            booking, payment.amount, now=at_boundary,
        )["restore_loyalty_points"])
        preview = self.client.get(url)
        self.cancel(url, preview.context["quote_key"])
        self.account.refresh_from_db()
        self.assertEqual(self.account.points_balance, 100)
        self.assertEqual(self.account.lifetime_points, 100)
        self.assertEqual(self.account.transactions.get(transaction_type="Reversal").remaining_points, 100)
        self.assertIn("Loyalty points returned: 100", mail.outbox[0].body)

        staff = get_user_model().objects.create_superuser(username="refund-staff")
        request = RequestFactory().post("/admin/payments/payment/")
        request.user = staff
        payment_admin = PaymentAdmin(Payment, admin.site)
        with patch.object(payment_admin, "message_user"):
            payment_admin.record_issued_refunds(request, Payment.objects.filter(pk=payment.pk))
        payment.refresh_from_db()
        booking.refresh_from_db()
        self.assertEqual(booking.refund_status, "Partially Refunded")
        self.assertEqual(payment.payment_status, "Partially Refunded")
        self.assertEqual(payment.refund_amount, Decimal("720.00"))
        self.assertIsNotNone(payment.refund_date)

    def test_stale_quote_or_ineligible_booking_cannot_be_cancelled(self):
        booking, _, url = self.make_booking(60)
        preview = self.client.get(url)
        with patch("apps.bookings.cancellation_services.timezone.now",
                   return_value=booking.departure_datetime - timedelta(hours=47)):
            self.cancel(url, preview.context["quote_key"])
        with patch("apps.bookings.cancellation_services.timezone.now",
                   return_value=booking.departure_datetime - timedelta(hours=3)):
            self.cancel(url, preview.context["quote_key"])
        booking.refresh_from_db()
        self.assertEqual(booking.booking_status, "Confirmed")
        self.assertFalse(self.user.notification_recipients.exists())

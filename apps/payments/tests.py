# Create your tests here.

from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import UserProfile
from apps.customers.models import Customer
from apps.bookings.models import Booking
from apps.payments.models import Payment


class CustomerPaymentTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.customer_user = User.objects.create_user(
            username="test_payment_customer",
            password="TestPassword123!",
            email="paymentcustomer@example.com",
        )

        UserProfile.objects.update_or_create(
            user=self.customer_user,
            defaults={"role": "Customer"},
        )

        self.customer = Customer.objects.create(
            user=self.customer_user,
            first_name="Payment",
            last_name="Customer",
            email="paymentcustomer@example.com",
            phone="0123456789",
            address="Test Address",
            city="Penang",
            state="Penang",
            postcode="11900",
            gender="Male",
        )

        travel_date = timezone.localdate() + timedelta(days=7)

        self.booking = Booking.objects.create(
            customer=self.customer,
            pickup_location="Penang Airport",
            destination="Penang Hill",
            travel_date=travel_date,
            departure_time="09:00",
            return_date=travel_date,
            passenger_count=20,
            total_price=Decimal("1000.00"),
            booking_status="Confirmed",
            payment_status="Pending",
        )

        self.client.force_login(self.customer_user)

    @patch("apps.payments.views.send_payment_receipt")
    def test_customer_can_complete_successful_payment(self, mock_receipt):

        response = self.client.post(
            reverse("payments:payment_create"),
            {
                "booking_id": self.booking.pk,
                "payment_method": "Online Banking",
                "simulation_result": "success",
            },
        )

        self.assertRedirects(
            response,
            reverse("payments:payment_list"),
        )

        self.booking.refresh_from_db()

        payment = Payment.objects.get(
            booking=self.booking,
            payment_status="Paid",
        )

        self.assertEqual(
            payment.amount,
            Decimal("1000.00"),
        )

        self.assertEqual(
            payment.payment_method,
            "Online Banking",
        )

        self.assertEqual(
            payment.payment_status,
            "Paid",
        )

        self.assertEqual(
            self.booking.payment_status,
            "Paid",
        )

        self.assertTrue(payment.transaction_id)

        mock_receipt.assert_called_once()

        print(
            "TC-P01: Customer payment completed successfully"
        )


    @patch("apps.payments.views.send_payment_receipt")
    def test_failed_payment_does_not_mark_booking_as_paid(self, mock_receipt):

        response = self.client.post(
            reverse("payments:payment_create"),
            {
                "booking_id": self.booking.pk,
                "payment_method": "Online Banking",
                "simulation_result": "failure",
            },
        )

        # Failed simulation returns to the payment form.
        self.assertEqual(response.status_code, 200)

        self.booking.refresh_from_db()

        # Booking must remain unpaid.
        self.assertEqual(
            self.booking.payment_status,
            "Pending",
        )

        # No successful payment should be recorded.
        self.assertFalse(
            Payment.objects.filter(
                booking=self.booking,
                payment_status="Paid",
            ).exists()
        )

        # A failed simulation should not create a new payment.
        self.assertEqual(
            Payment.objects.filter(
                booking=self.booking,
            ).count(),
            0,
        )

        # No receipt should be emailed.
        mock_receipt.assert_not_called()

        print(
            "TC-P02: Failed payment simulation handled successfully"
        )


    @patch("apps.payments.views.send_payment_receipt")
    def test_customer_cannot_pay_same_booking_twice(self, mock_receipt):

        payment_url = reverse("payments:payment_create")

        payment_data = {
            "booking_id": self.booking.pk,
            "payment_method": "Online Banking",
            "simulation_result": "success",
        }

        # First payment should succeed.
        first_response = self.client.post(
            payment_url,
            payment_data,
        )

        self.assertRedirects(
            first_response,
            reverse("payments:payment_list"),
        )

        self.booking.refresh_from_db()

        self.assertEqual(
            self.booking.payment_status,
            "Paid",
        )

        self.assertEqual(
            Payment.objects.filter(
                booking=self.booking,
                payment_status="Paid",
            ).count(),
            1,
        )

        first_payment = Payment.objects.get(
            booking=self.booking,
            payment_status="Paid",
        )

        first_transaction_id = first_payment.transaction_id

        # Attempt to pay for the same booking again.
        second_response = self.client.post(
            payment_url,
            payment_data,
        )

        # The second payment must be rejected.
        self.assertRedirects(
            second_response,
            reverse("bookings:customer_bookings"),
        )

        self.booking.refresh_from_db()

        # Booking remains paid.
        self.assertEqual(
            self.booking.payment_status,
            "Paid",
        )

        # There must still be only one paid transaction.
        self.assertEqual(
            Payment.objects.filter(
                booking=self.booking,
                payment_status="Paid",
            ).count(),
            1,
        )

        first_payment.refresh_from_db()

        # Original transaction ID must remain unchanged.
        self.assertEqual(
            first_payment.transaction_id,
            first_transaction_id,
        )

        # Receipt email should only be triggered once.
        mock_receipt.assert_called_once()

        print(
            "TC-P03: Duplicate payment successfully prevented"
        )


    @patch("apps.payments.views.send_payment_receipt")
    def test_customer_cannot_pay_another_customers_booking(self, mock_receipt):

        User = get_user_model()

        other_user = User.objects.create_user(
            username="test_other_payment_customer",
            password="TestPassword123!",
            email="othercustomer@example.com",
        )

        UserProfile.objects.update_or_create(
            user=other_user,
            defaults={"role": "Customer"},
        )

        other_customer = Customer.objects.create(
            user=other_user,
            first_name="Other",
            last_name="Customer",
            email="othercustomer@example.com",
            phone="0198765432",
            address="Other Test Address",
            city="Penang",
            state="Penang",
            postcode="11900",
            gender="Male",
        )

        # Log in as Customer B.
        self.client.force_login(other_user)

        # Attempt to pay for Customer A's booking.
        response = self.client.post(
            reverse("payments:payment_create"),
            {
                "booking_id": self.booking.pk,
                "payment_method": "Online Banking",
                "simulation_result": "success",
            },
        )

        # Booking ownership protection should return HTTP 404.
        self.assertEqual(response.status_code, 404)

        self.booking.refresh_from_db()

        # Original booking must remain unpaid.
        self.assertEqual(
            self.booking.payment_status,
            "Pending",
        )

        # No payment should be created.
        self.assertFalse(
            Payment.objects.filter(
                booking=self.booking,
            ).exists()
        )

        # No receipt should be sent.
        mock_receipt.assert_not_called()

        print(
            "TC-P04: Unauthorized customer payment access prevented"
        )


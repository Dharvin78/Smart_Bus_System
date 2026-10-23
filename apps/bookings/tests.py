# Create your tests here.

from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import UserProfile
from apps.bookings.models import Booking
from apps.customers.models import Customer

from apps.vehicles.models import Vehicle
from apps.drivers.models import Driver
from apps.payments.models import Payment

class CustomerBookingTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.customer_user = User.objects.create_user(
            username="test_booking_customer",
            password="TestPassword123!",
            email="customer@example.com",
        )

        UserProfile.objects.update_or_create(
            user=self.customer_user,
            defaults={"role": "Customer"},
        )

        self.customer = Customer.objects.create(
            user=self.customer_user,
            first_name="Test",
            last_name="Customer",
            email="customer@example.com",
            phone="0123456789",
            address="Test Address",
            city="Penang",
            state="Penang",
            postcode="11900",
            gender="Male",
        )

        self.client.force_login(self.customer_user)

    @patch("apps.bookings.views.send_booking_submitted_email")
    @patch("apps.bookings.views.notify_booking_staff")
    @patch("apps.bookings.views.notify_customer")
    
    def test_customer_can_submit_booking(
        self,
        mock_notify_customer,
        mock_notify_staff,
        mock_send_email,
    ):
        mock_send_email.return_value = True

        travel_date = timezone.localdate() + timedelta(days=7)

        response = self.client.post(
            reverse("bookings:booking_create"),
            {
                "pickup_location": "Penang Airport",
                "destination": "Penang Hill",
                "travel_date": travel_date.isoformat(),
                "departure_time": "09:00",
                "return_date": travel_date.isoformat(),
                "passenger_count": 20,
                "remarks": "FYP automated test",
            },
        )

        self.assertRedirects(
            response,
            reverse("bookings:customer_bookings"),
        )

        self.assertEqual(Booking.objects.count(), 1)

        booking = Booking.objects.get()

        self.assertEqual(booking.customer, self.customer)
        self.assertEqual(booking.booking_status, "Pending")
        self.assertEqual(booking.payment_status, "Pending")
        self.assertIsNone(booking.vehicle)
        self.assertIsNone(booking.driver)
        self.assertEqual(booking.total_price, Decimal("0.00"))
        self.assertEqual(booking.passenger_count, 20)
        self.assertTrue(booking.booking_number)

        print("TC-B01: Customer booking submitted successfully")

    def test_booking_rejects_more_than_42_passengers(self):
        travel_date = timezone.localdate() + timedelta(days=7)

        response = self.client.post(
            reverse("bookings:booking_create"),
            {
                "pickup_location": "Penang Airport",
                "destination": "Penang Hill",
                "travel_date": travel_date.isoformat(),
                "departure_time": "09:00",
                "return_date": travel_date.isoformat(),
                "passenger_count": 43,
                "remarks": "Testing passenger limit",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Booking.objects.count(), 0)

        self.assertIn("passenger_count", response.context["form"].errors)

        print("TC-B02: Booking with 43 passengers rejected successfully")

    
    def test_owner_can_approve_pending_booking(self):
        User = get_user_model()

        owner = User.objects.create_user(
            username="test_booking_owner",
            password="TestPassword123!",
        )

        UserProfile.objects.update_or_create(
            user=owner,
            defaults={"role": "Owner"},
        )

        travel_date = timezone.localdate() + timedelta(days=7)
        expiry_date = timezone.localdate() + timedelta(days=365)

        vehicle = Vehicle.objects.create(
            registration_number="TCB03001",
            vehicle_name="Test Approval Bus",
            bus_type="Standard Bus",
            seat_capacity=44,
            manufacture_year=2024,
            insurance_expiry=expiry_date,
            road_tax_expiry=expiry_date,
            status="Available",
        )

        driver = Driver.objects.create(
            full_name="Test Approval Driver",
            ic_passport="TCB03IC001",
            phone="0123456789",
            driving_license="TCB03LIC001",
            license_expiry=expiry_date,
            status="Available",
        )

        booking = Booking.objects.create(
            customer=self.customer,
            pickup_location="Penang Airport",
            destination="Penang Hill",
            travel_date=travel_date,
            departure_time="09:00",
            return_date=travel_date,
            passenger_count=20,
            total_price=Decimal("0.00"),
            booking_status="Pending",
            payment_status="Pending",
        )

        owner.refresh_from_db()
        owner.profile.refresh_from_db()

        self.assertEqual(owner.profile.role, "Owner")

        self.client.force_login(owner)

        response = self.client.post(
            reverse("bookings:booking_review", args=[booking.pk]),
            {
                "action": "approve",
                "vehicle": vehicle.pk,
                "driver": driver.pk,
                "total_price": "1000.00",
                "approval_notes": "Approved during FYP testing",
            },
        )

        print("Owner role:", owner.profile.role)
        print("Authenticated:", owner.is_authenticated)
        print("Response status:", response.status_code)
        print("Response body:", response.content.decode("utf-8")[:500])

        self.assertRedirects(
            response,
            reverse("bookings:booking_list"),
        )

        booking.refresh_from_db()
        vehicle.refresh_from_db()
        driver.refresh_from_db()

        self.assertEqual(booking.booking_status, "Confirmed")
        self.assertEqual(booking.payment_status, "Pending")
        self.assertEqual(booking.vehicle, vehicle)
        self.assertEqual(booking.driver, driver)
        self.assertEqual(booking.total_price, Decimal("1000.00"))

        self.assertIsNotNone(booking.approval_time)
        self.assertIsNotNone(booking.payment_deadline)

        self.assertEqual(vehicle.status, "Booked")
        self.assertEqual(driver.status, "Reserved")

        payment = Payment.objects.get(booking=booking)
        self.assertEqual(payment.amount, Decimal("1000.00"))
        self.assertEqual(payment.payment_status, "Pending")

        print("TC-B03: Owner approved pending booking successfully")

    def test_owner_can_reject_pending_booking(self):
        User = get_user_model()

        owner = User.objects.create_user(
            username="test_rejection_owner",
            password="TestPassword123!",
        )

        UserProfile.objects.update_or_create(
            user=owner,
            defaults={"role": "Owner"},
        )

        travel_date = timezone.localdate() + timedelta(days=7)

        booking = Booking.objects.create(
            customer=self.customer,
            pickup_location="Penang Airport",
            destination="Penang Hill",
            travel_date=travel_date,
            departure_time="09:00",
            return_date=travel_date,
            passenger_count=20,
            total_price=Decimal("0.00"),
            booking_status="Pending",
            payment_status="Pending",
        )

        owner.refresh_from_db()
        owner.profile.refresh_from_db()
        self.client.force_login(owner)

        response = self.client.post(
            reverse("bookings:booking_review", args=[booking.pk]),
            {
                "action": "reject",
                "reason": "Vehicle unavailable for requested date",
            },
        )

        self.assertRedirects(
            response,
            reverse("bookings:booking_list"),
        )

        booking.refresh_from_db()

        self.assertEqual(booking.booking_status, "Cancelled")
        self.assertEqual(
            booking.rejection_reason,
            "Vehicle unavailable for requested date",
        )
        self.assertIsNotNone(booking.cancelled_at)
        self.assertIsNone(booking.vehicle)
        self.assertIsNone(booking.driver)

        print("TC-B04: Owner rejected pending booking successfully")
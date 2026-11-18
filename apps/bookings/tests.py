# Create your tests here.

from datetime import timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core import mail
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

    def post_and_send_updates(self, url, data):
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(url, data)

    def assert_customer_update(self, booking, title, detail):
        recipient = self.customer_user.notification_recipients.get()
        notification = recipient.notification
        self.assertEqual(notification.title, title)
        self.assertEqual(notification.link, reverse("bookings:customer_bookings"))
        self.assertIn(booking.booking_number, notification.message)
        self.assertIn(detail, notification.message)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, [self.customer.email])
        self.assertEqual(email.subject, f"{title} - {booking.booking_number}")
        self.assertIn(detail, email.body)
        self.assertEqual(email.alternatives[0].mimetype, "text/html")
        self.assertIn(detail, email.alternatives[0].content)
        self.assertIn("Open My Bookings", email.alternatives[0].content)

    def test_customer_can_submit_booking(self):
        travel_date = timezone.localdate() + timedelta(days=7)

        response = self.post_and_send_updates(
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
        self.assert_customer_update(booking, "Booking Request Received", "awaiting staff review")

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

    
    def approve_pending_booking(self):
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
            phone="0123456789",
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

        response = self.post_and_send_updates(
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

        return booking, vehicle, driver

    def test_approval_sends_customer_update_with_price_and_deadline(self):
        booking, _, _ = self.approve_pending_booking()
        booking.refresh_from_db()
        self.assert_customer_update(booking, "Booking Approved", "RM 1,000.00")
        deadline = timezone.localtime(booking.payment_deadline)
        self.assertIn(f"{deadline:%d %b %Y, %I:%M %p %Z}", mail.outbox[0].body)

    def test_owner_can_approve_pending_booking(self):
        booking, vehicle, driver = self.approve_pending_booking()
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

        review_url = reverse("bookings:booking_review", args=[booking.pk])
        review_data = {
            "action": "reject",
            "reason": "Vehicle unavailable for requested date",
        }
        response = self.post_and_send_updates(
            review_url, review_data,
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
        self.post_and_send_updates(review_url, review_data)
        self.assert_customer_update(booking, "Booking Rejected", booking.rejection_reason)

        print("TC-B04: Owner rejected pending booking successfully")

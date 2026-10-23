# Create your tests here.

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import UserProfile
from apps.drivers.models import Driver

from decimal import Decimal
from apps.customers.models import Customer
from apps.bookings.models import Booking
from apps.drivers.models import DriverReview

class DriverManagementTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.owner = User.objects.create_user(
            username="test_driver_owner",
            password="TestPassword123!",
            email="driverowner@example.com",
        )

        UserProfile.objects.update_or_create(
            user=self.owner,
            defaults={"role": "Owner"},
        )

        self.owner.refresh_from_db()
        self.client.force_login(self.owner)

    def test_owner_can_create_driver(self):

        expiry_date = timezone.localdate() + timedelta(days=365)

        response = self.client.post(
            reverse("drivers:driver_create"),
            {
                "full_name": "Test Driver One",
                "ic_passport": "TC-D01-IC001",
                "phone": "0123456789",
                "email": "testdriver@example.com",
                "address": "Penang, Malaysia",
                "driving_license": "TC-D01-LIC001",
                "license_expiry": expiry_date.isoformat(),
                "status": "Available",
            },
        )

        self.assertRedirects(
            response,
            reverse("drivers:driver_list"),
        )

        self.assertEqual(Driver.objects.count(), 1)

        driver = Driver.objects.get(
            ic_passport="TC-D01-IC001"
        )

        self.assertEqual(
            driver.full_name,
            "Test Driver One",
        )

        self.assertEqual(
            driver.driving_license,
            "TC-D01-LIC001",
        )

        self.assertEqual(
            driver.phone,
            "0123456789",
        )

        self.assertEqual(
            driver.status,
            "Available",
        )

        self.assertEqual(
            driver.license_expiry,
            expiry_date,
        )

        self.assertIsNone(driver.assigned_vehicle)

        print("TC-D01: Owner created driver successfully")


    def test_owner_can_update_driver(self):

        expiry_date = timezone.localdate() + timedelta(days=365)

        driver = Driver.objects.create(
            full_name="Original Driver",
            ic_passport="TC-D02-IC001",
            phone="0123456789",
            email="original@example.com",
            address="Penang",
            driving_license="TC-D02-LIC001",
            license_expiry=expiry_date,
            status="Available",
        )

        new_expiry_date = timezone.localdate() + timedelta(days=730)

        response = self.client.post(
            reverse("drivers:driver_update", args=[driver.pk]),
            {
                "full_name": "Updated Driver",
                "ic_passport": "TC-D02-IC001",
                "phone": "0198765432",
                "email": "updated@example.com",
                "address": "Bukit Mertajam, Penang",
                "driving_license": "TC-D02-LIC001",
                "license_expiry": new_expiry_date.isoformat(),
                "status": "Leave",
            },
        )

        self.assertRedirects(
            response,
            reverse("drivers:driver_list"),
        )

        driver.refresh_from_db()

        self.assertEqual(
            driver.full_name,
            "Updated Driver",
        )

        self.assertEqual(
            driver.phone,
            "0198765432",
        )

        self.assertEqual(
            driver.email,
            "updated@example.com",
        )

        self.assertEqual(
            driver.address,
            "Bukit Mertajam, Penang",
        )

        self.assertEqual(
            driver.license_expiry,
            new_expiry_date,
        )

        self.assertEqual(
            driver.status,
            "Leave",
        )

        self.assertEqual(Driver.objects.count(), 1)

        print("TC-D02: Owner updated driver successfully")


    def test_owner_can_delete_driver(self):

        expiry_date = timezone.localdate() + timedelta(days=365)

        driver = Driver.objects.create(
            full_name="Test Driver To Delete",
            ic_passport="TC-D03-IC001",
            phone="0123456789",
            email="delete@example.com",
            address="Penang",
            driving_license="TC-D03-LIC001",
            license_expiry=expiry_date,
            status="Available",
        )

        driver_id = driver.pk

        # Confirm driver exists before deletion.
        self.assertTrue(
            Driver.objects.filter(pk=driver_id).exists()
        )

        # Owner submits deletion request.
        response = self.client.post(
            reverse(
                "drivers:driver_delete",
                args=[driver_id],
            )
        )

        # Successful deletion redirects to driver list.
        self.assertRedirects(
            response,
            reverse("drivers:driver_list"),
        )

        # Driver should no longer exist.
        self.assertFalse(
            Driver.objects.filter(pk=driver_id).exists()
        )

        self.assertEqual(
            Driver.objects.count(),
            0,
        )

        print("TC-D03: Owner deleted driver successfully")


    def test_customer_cannot_manage_drivers(self):

        User = get_user_model()

        customer_user = User.objects.create_user(
            username="test_driver_customer",
            password="TestPassword123!",
            email="drivercustomer@example.com",
        )

        UserProfile.objects.update_or_create(
            user=customer_user,
            defaults={"role": "Customer"},
        )

        expiry_date = timezone.localdate() + timedelta(days=365)

        driver = Driver.objects.create(
            full_name="Protected Driver",
            ic_passport="TC-D04-IC001",
            phone="0123456789",
            email="protected@example.com",
            address="Penang",
            driving_license="TC-D04-LIC001",
            license_expiry=expiry_date,
            status="Available",
        )

        self.client.force_login(customer_user)

        # Attempt 1: Unauthorized driver creation.
        create_response = self.client.post(
            reverse("drivers:driver_create"),
            {
                "full_name": "Unauthorized Driver",
                "ic_passport": "TC-D04-IC002",
                "phone": "0198765432",
                "driving_license": "TC-D04-LIC002",
                "license_expiry": expiry_date.isoformat(),
                "status": "Available",
            },
        )

        # Attempt 2: Unauthorized driver update.
        update_response = self.client.post(
            reverse("drivers:driver_update", args=[driver.pk]),
            {
                "full_name": "Modified Without Permission",
                "ic_passport": "TC-D04-IC001",
                "phone": "0198765432",
                "driving_license": "TC-D04-LIC001",
                "license_expiry": expiry_date.isoformat(),
                "status": "Inactive",
            },
        )

        # Attempt 3: Unauthorized driver deletion.
        delete_response = self.client.post(
            reverse("drivers:driver_delete", args=[driver.pk]),
        )

        # Unauthorized requests should be forbidden.
        self.assertEqual(create_response.status_code, 403)
        self.assertEqual(update_response.status_code, 403)
        self.assertEqual(delete_response.status_code, 403)

        # No unauthorized driver should be created.
        self.assertEqual(Driver.objects.count(), 1)

        # Original driver must remain unchanged.
        driver.refresh_from_db()

        self.assertEqual(driver.full_name, "Protected Driver")
        self.assertEqual(driver.phone, "0123456789")
        self.assertEqual(driver.status, "Available")

        print(
            "TC-D04: Unauthorized driver management access prevented"
        )



class DriverReviewTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.customer_user = User.objects.create_user(
            username="test_review_customer",
            password="TestPassword123!",
            email="reviewcustomer@example.com",
        )

        UserProfile.objects.update_or_create(
            user=self.customer_user,
            defaults={"role": "Customer"},
        )

        self.customer = Customer.objects.create(
            user=self.customer_user,
            first_name="Review",
            last_name="Customer",
            email="reviewcustomer@example.com",
            phone="0123456789",
            address="Penang",
            city="Penang",
            state="Penang",
            postcode="11900",
            gender="Male",
        )

        expiry_date = timezone.localdate() + timedelta(days=365)

        self.driver = Driver.objects.create(
            full_name="Review Test Driver",
            ic_passport="TC-D05-IC001",
            phone="0123456789",
            driving_license="TC-D05-LIC001",
            license_expiry=expiry_date,
            status="Available",
        )

        travel_date = timezone.localdate() - timedelta(days=1)

        self.booking = Booking.objects.create(
            customer=self.customer,
            driver=self.driver,
            pickup_location="Penang Airport",
            destination="Penang Hill",
            travel_date=travel_date,
            departure_time="09:00",
            return_date=travel_date,
            passenger_count=20,
            total_price=Decimal("1000.00"),
            booking_status="Completed",
            payment_status="Paid",
        )

        self.client.force_login(self.customer_user)

    def test_customer_can_review_completed_booking(self):

        response = self.client.post(
            reverse(
                "drivers:driver_review",
                args=[self.booking.pk],
            ),
            {
                "rating": 5,
                "comment": "Excellent driving and professional service.",
            },
        )

        self.assertRedirects(
            response,
            reverse("bookings:customer_bookings"),
        )

        self.assertEqual(DriverReview.objects.count(), 1)

        review = DriverReview.objects.get(
            booking=self.booking,
        )

        self.assertEqual(review.rating, 5)

        self.assertEqual(
            review.comment,
            "Excellent driving and professional service.",
        )

        self.assertEqual(
            review.booking.driver,
            self.driver,
        )

        print(
            "TC-D05: Customer driver review submitted successfully"
        )


    def test_customer_cannot_review_same_booking_twice(self):

        review_url = reverse(
            "drivers:driver_review",
            args=[self.booking.pk],
        )

        # First review submission.
        first_response = self.client.post(
            review_url,
            {
                "rating": 5,
                "comment": "Excellent service.",
            },
        )

        self.assertRedirects(
            first_response,
            reverse("bookings:customer_bookings"),
        )

        self.assertEqual(DriverReview.objects.count(), 1)

        original_review = DriverReview.objects.get(
            booking=self.booking,
        )

        original_review_id = original_review.pk

        # Second review submission for the same booking.
        second_response = self.client.post(
            review_url,
            {
                "rating": 1,
                "comment": "Attempted duplicate review.",
            },
        )

        # Duplicate submission should be redirected.
        self.assertRedirects(
            second_response,
            reverse("bookings:customer_bookings"),
        )

        # Only one review should exist.
        self.assertEqual(DriverReview.objects.count(), 1)

        original_review.refresh_from_db()

        # Original review must remain unchanged.
        self.assertEqual(original_review.pk, original_review_id)
        self.assertEqual(original_review.rating, 5)
        self.assertEqual(
            original_review.comment,
            "Excellent service.",
        )

        print(
            "TC-D06: Duplicate driver review successfully prevented"
        )


    def test_driver_review_rejects_invalid_ratings(self):

        review_url = reverse(
            "drivers:driver_review",
            args=[self.booking.pk],
        )

        # Test ratings outside the permitted range.
        for invalid_rating in [0, 6]:

            with self.subTest(rating=invalid_rating):

                response = self.client.post(
                    review_url,
                    {
                        "rating": invalid_rating,
                        "comment": "Invalid rating test",
                    },
                )

                # Invalid form should be displayed again.
                self.assertEqual(response.status_code, 200)

                # No review should be saved.
                self.assertFalse(
                    DriverReview.objects.filter(
                        booking=self.booking
                    ).exists()
                )

                # Verify that the form reports a rating error.
                self.assertIn(
                    "rating",
                    response.context["form"].errors,
                )

        print(
            "TC-D07: Invalid driver ratings rejected successfully"
        )


    def test_customer_cannot_review_another_customers_booking(self):

        User = get_user_model()

        # Create Customer B.
        other_user = User.objects.create_user(
            username="test_other_review_customer",
            password="TestPassword123!",
            email="otherreview@example.com",
        )

        UserProfile.objects.update_or_create(
            user=other_user,
            defaults={"role": "Customer"},
        )

        other_customer = Customer.objects.create(
            user=other_user,
            first_name="Other",
            last_name="Customer",
            email="otherreview@example.com",
            phone="0198765432",
            address="Penang",
            city="Penang",
            state="Penang",
            postcode="11900",
            gender="Male",
        )

        # Log in as Customer B.
        self.client.force_login(other_user)

        # Attempt to review Customer A's completed booking.
        response = self.client.post(
            reverse(
                "drivers:driver_review",
                args=[self.booking.pk],
            ),
            {
                "rating": 1,
                "comment": "Unauthorized review attempt",
            },
        )

        # Ownership protection should return HTTP 404.
        self.assertEqual(response.status_code, 404)

        # No unauthorized review should be created.
        self.assertFalse(
            DriverReview.objects.filter(
                booking=self.booking
            ).exists()
        )

        self.assertEqual(DriverReview.objects.count(), 0)

        # Original booking remains unchanged.
        self.booking.refresh_from_db()

        self.assertEqual(
            self.booking.customer,
            self.customer,
        )

        self.assertEqual(
            self.booking.booking_status,
            "Completed",
        )

        print(
            "TC-D08: Unauthorized driver review access prevented"
        )

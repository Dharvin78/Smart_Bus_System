from django.test import TestCase
from django.urls import reverse

from apps.bookings.models import Booking
from apps.customers.models import Customer
from apps.drivers.models import Driver
from apps.vehicles.models import Vehicle

from django.contrib.auth.models import User
from apps.accounts.models import UserProfile
from django.contrib.auth import get_user_model

from datetime import timedelta
from django.utils import timezone
from django.urls import reverse

class VehicleListBookingStatusTests(TestCase):

    def setUp(self):

        User = get_user_model()

        self.owner_user = User.objects.create_user(
            username="test_vehicle_owner",
            password="TestPassword123!",
        )

        UserProfile.objects.update_or_create(
            user=self.owner_user,
            defaults={"role": "Owner"},
        )

        self.owner_user.refresh_from_db()
        self.client.force_login(self.owner_user)

    def test_vehicle_list_displays_operational_status(self):
        vehicle = Vehicle.objects.create(
            registration_number="VBL9999",
            vehicle_name="Test Bus",
            bus_type="Mini Bus",
            seat_capacity=30,
            manufacture_year=2022,
            insurance_expiry="2030-01-01",
            road_tax_expiry="2030-01-01",
            status="Available",
        )

        customer = Customer.objects.create(
            first_name="Asha",
            last_name="Khan",
            email="asha@example.com",
            phone="0123456789",
            address="Test address",
            city="Kuala Lumpur",
            state="KL",
            postcode="50000",
            gender="Female",
        )

        driver = Driver.objects.create(
            full_name="Rahim",
            ic_passport="A1234567",
            phone="0111111111",
            email="rahim@example.com",
            address="Driver address",
            driving_license="DL12345",
            license_expiry="2030-01-01",
            status="Available",
        )

        Booking.objects.create(
            customer=customer,
            vehicle=vehicle,
            driver=driver,
            pickup_location="Station A",
            destination="Station B",
            travel_date="2026-08-01",
            departure_time="08:00:00",
            passenger_count=10,
            booking_status="Confirmed",
            payment_status="Paid",
        )

        response = self.client.get(reverse("vehicles:vehicle_list"))

        print("Logged-in user:", self.owner_user.username)
        print("User role:", self.owner_user.profile.role)
        print("Authenticated:", self.owner_user.is_authenticated)
        print("HTTP status:", response.status_code)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "VBL9999")
        self.assertContains(response, "Test Bus")
        self.assertContains(response, "Available")


    def test_owner_can_create_vehicle(self):

        expiry_date = timezone.localdate() + timedelta(days=365)

        response = self.client.post(
            reverse("vehicles:vehicle_create"),
            {
                "registration_number": "TCV02001",
                "vehicle_name": "Test Standard Bus",
                "bus_type": "Standard Bus",
                "seat_capacity": 44,
                "manufacture_year": 2024,
                "insurance_expiry": expiry_date.isoformat(),
                "road_tax_expiry": expiry_date.isoformat(),
                "status": "Available",
            },
        )

        self.assertRedirects(
            response,
            reverse("vehicles:vehicle_list"),
        )

        vehicle = Vehicle.objects.get(
            registration_number="TCV02001"
        )

        self.assertEqual(
            vehicle.vehicle_name,
            "Test Standard Bus",
        )

        self.assertEqual(
            vehicle.bus_type,
            "Standard Bus",
        )

        self.assertEqual(
            vehicle.seat_capacity,
            44,
        )

        self.assertEqual(
            vehicle.manufacture_year,
            2024,
        )

        self.assertEqual(
            vehicle.insurance_expiry,
            expiry_date,
        )

        self.assertEqual(
            vehicle.road_tax_expiry,
            expiry_date,
        )

        self.assertEqual(
            vehicle.status,
            "Available",
        )

        print("TC-V02: Owner created vehicle successfully")


    def test_owner_can_update_vehicle(self):

        expiry_date = timezone.localdate() + timedelta(days=365)

        vehicle = Vehicle.objects.create(
            registration_number="TCV03001",
            vehicle_name="Original Test Bus",
            bus_type="Standard Bus",
            seat_capacity=44,
            manufacture_year=2023,
            insurance_expiry=expiry_date,
            road_tax_expiry=expiry_date,
            status="Available",
        )

        new_expiry_date = timezone.localdate() + timedelta(days=730)

        response = self.client.post(
            reverse("vehicles:vehicle_update", args=[vehicle.pk]),
            {
                "registration_number": "TCV03001",
                "vehicle_name": "Updated VIP Coach",
                "bus_type": "VIP Coach",
                "seat_capacity": 30,
                "manufacture_year": 2024,
                "insurance_expiry": new_expiry_date.isoformat(),
                "road_tax_expiry": new_expiry_date.isoformat(),
                "status": "Maintenance",
            },
        )

        self.assertRedirects(
            response,
            reverse("vehicles:vehicle_list"),
        )

        vehicle.refresh_from_db()

        self.assertEqual(
            vehicle.vehicle_name,
            "Updated VIP Coach",
        )

        self.assertEqual(
            vehicle.bus_type,
            "VIP Coach",
        )

        self.assertEqual(
            vehicle.seat_capacity,
            30,
        )

        self.assertEqual(
            vehicle.manufacture_year,
            2024,
        )

        self.assertEqual(
            vehicle.insurance_expiry,
            new_expiry_date,
        )

        self.assertEqual(
            vehicle.road_tax_expiry,
            new_expiry_date,
        )

        self.assertEqual(
            vehicle.status,
            "Maintenance",
        )

        self.assertEqual(
            Vehicle.objects.count(),
            1,
        )

        print("TC-V03: Owner updated vehicle successfully")


    def test_owner_can_delete_vehicle(self):

        expiry_date = timezone.localdate() + timedelta(days=365)

        vehicle = Vehicle.objects.create(
            registration_number="TCV04001",
            vehicle_name="Test Vehicle To Delete",
            bus_type="Standard Bus",
            seat_capacity=44,
            manufacture_year=2024,
            insurance_expiry=expiry_date,
            road_tax_expiry=expiry_date,
            status="Available",
        )

        vehicle_id = vehicle.pk

        # Verify vehicle exists before deletion.
        self.assertTrue(
            Vehicle.objects.filter(pk=vehicle_id).exists()
        )

        # Owner submits vehicle deletion request.
        response = self.client.post(
            reverse(
                "vehicles:vehicle_delete",
                args=[vehicle_id],
            )
        )

        # Successful deletion redirects to vehicle list.
        self.assertRedirects(
            response,
            reverse("vehicles:vehicle_list"),
        )

        # Vehicle should no longer exist.
        self.assertFalse(
            Vehicle.objects.filter(pk=vehicle_id).exists()
        )

        self.assertEqual(
            Vehicle.objects.count(),
            0,
        )

        print("TC-V04: Owner deleted vehicle successfully")


    def test_duplicate_vehicle_registration_is_rejected(self):

        expiry_date = timezone.localdate() + timedelta(days=365)

        # Create an existing vehicle.
        Vehicle.objects.create(
            registration_number="TCV05001",
            vehicle_name="Existing Test Bus",
            bus_type="Standard Bus",
            seat_capacity=44,
            manufacture_year=2024,
            insurance_expiry=expiry_date,
            road_tax_expiry=expiry_date,
            status="Available",
        )

        # Attempt to register another vehicle
        # using the same registration number.
        response = self.client.post(
            reverse("vehicles:vehicle_create"),
            {
                "registration_number": "TCV05001",
                "vehicle_name": "Duplicate Test Bus",
                "bus_type": "VIP Coach",
                "seat_capacity": 30,
                "manufacture_year": 2025,
                "insurance_expiry": expiry_date.isoformat(),
                "road_tax_expiry": expiry_date.isoformat(),
                "status": "Available",
            },
        )

        # Invalid form should display the form again.
        self.assertEqual(response.status_code, 200)

        # The registration number must have a validation error.
        self.assertIn(
            "registration_number",
            response.context["form"].errors,
        )

        # No duplicate vehicle should be created.
        self.assertEqual(
            Vehicle.objects.filter(
                registration_number="TCV05001"
            ).count(),
            1,
        )

        # Original vehicle details remain unchanged.
        vehicle = Vehicle.objects.get(
            registration_number="TCV05001"
        )

        self.assertEqual(
            vehicle.vehicle_name,
            "Existing Test Bus",
        )

        print(
            "TC-V05: Duplicate vehicle registration rejected successfully"
        )


    def test_customer_cannot_manage_vehicles(self):

        User = get_user_model()

        # Create a customer account.
        customer_user = User.objects.create_user(
            username="test_vehicle_customer",
            password="TestPassword123!",
            email="vehiclecustomer@example.com",
        )

        UserProfile.objects.update_or_create(
            user=customer_user,
            defaults={"role": "Customer"},
        )

        expiry_date = timezone.localdate() + timedelta(days=365)

        # Create a vehicle to test update/delete permissions.
        vehicle = Vehicle.objects.create(
            registration_number="TCV06001",
            vehicle_name="Protected Test Bus",
            bus_type="Standard Bus",
            seat_capacity=44,
            manufacture_year=2024,
            insurance_expiry=expiry_date,
            road_tax_expiry=expiry_date,
            status="Available",
        )

        # Log in as Customer instead of Owner.
        self.client.force_login(customer_user)

        # Test unauthorized access to all vehicle operations.
        urls = [
            reverse("vehicles:vehicle_list"),
            reverse("vehicles:vehicle_create"),
            reverse("vehicles:vehicle_update", args=[vehicle.pk]),
            reverse("vehicles:vehicle_delete", args=[vehicle.pk]),
        ]

        for url in urls:
            with self.subTest(url=url):

                response = self.client.get(url)

                # Customer must not access the management page.
                self.assertNotEqual(response.status_code, 200)

        # Attempt unauthorized vehicle creation.
        response = self.client.post(
            reverse("vehicles:vehicle_create"),
            {
                "registration_number": "TCV06002",
                "vehicle_name": "Unauthorized Bus",
                "bus_type": "Mini Bus",
                "seat_capacity": 20,
                "manufacture_year": 2024,
                "insurance_expiry": expiry_date.isoformat(),
                "road_tax_expiry": expiry_date.isoformat(),
                "status": "Available",
            },
        )

        self.assertNotEqual(response.status_code, 200)

        self.assertFalse(
            Vehicle.objects.filter(
                registration_number="TCV06002"
            ).exists()
        )

        # Attempt unauthorized vehicle update.
        response = self.client.post(
            reverse("vehicles:vehicle_update", args=[vehicle.pk]),
            {
                "registration_number": "TCV06001",
                "vehicle_name": "Unauthorized Update",
                "bus_type": "VIP Coach",
                "seat_capacity": 30,
                "manufacture_year": 2025,
                "insurance_expiry": expiry_date.isoformat(),
                "road_tax_expiry": expiry_date.isoformat(),
                "status": "Inactive",
            },
        )

        self.assertNotEqual(response.status_code, 200)

        # Attempt unauthorized vehicle deletion.
        response = self.client.post(
            reverse("vehicles:vehicle_delete", args=[vehicle.pk])
        )

        self.assertNotEqual(response.status_code, 200)

        # Verify original vehicle remains unchanged.
        vehicle.refresh_from_db()

        self.assertEqual(
            vehicle.vehicle_name,
            "Protected Test Bus",
        )

        self.assertEqual(vehicle.status, "Available")

        self.assertEqual(Vehicle.objects.count(), 1)

        print(
            "TC-V06: Customer blocked from vehicle management"
        )

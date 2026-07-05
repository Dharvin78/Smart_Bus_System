from django.test import TestCase
from django.urls import reverse

from apps.bookings.models import Booking
from apps.customers.models import Customer
from apps.drivers.models import Driver
from apps.vehicles.models import Vehicle


class VehicleListBookingStatusTests(TestCase):

    def test_vehicle_list_displays_latest_booking_status(self):
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

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Confirmed")

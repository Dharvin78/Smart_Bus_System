# Create your tests here.


from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import UserProfile
from apps.vehicles.models import Vehicle
from apps.fuel.models import Fuel


class FuelManagementTests(TestCase):

    def setUp(self):
        User = get_user_model()

        # Create Owner
        self.owner = User.objects.create_user(
            username="test_fuel_owner",
            password="TestPassword123!",
            email="fuelowner@example.com",
        )

        UserProfile.objects.update_or_create(
            user=self.owner,
            defaults={"role": "Owner"},
        )

        # Create Customer
        self.customer = User.objects.create_user(
            username="test_fuel_customer",
            password="TestPassword123!",
            email="fuelcustomer@example.com",
        )

        owner_profile, _ = UserProfile.objects.update_or_create(
            user=self.owner,
            defaults={"role": "Owner"},
        )

        owner_profile.refresh_from_db()
        self.owner.refresh_from_db()

        self.assertEqual(owner_profile.role, "Owner")

        today = timezone.localdate()

        self.vehicle = Vehicle.objects.create(
            registration_number="TCF00001",
            vehicle_name="Fuel Test Bus",
            bus_type="Standard Bus",
            seat_capacity=44,
            manufacture_year=2024,
            insurance_expiry=today + timedelta(days=365),
            road_tax_expiry=today + timedelta(days=365),
            status="Available",
        )

        self.refill_date = today

        # Log in as Owner for each test
        self.client.force_login(self.owner)

    def fuel_data(self, **overrides):
        data = {
            "vehicle": self.vehicle.pk,
            "fuel_type": "Diesel",
            "refill_date": self.refill_date.isoformat(),
            "litres": "100.00",
            "price_per_litre": "2.50",
            "fuel_station": "Penang Fuel Station",
            "mileage": 50000,
            "remarks": "Routine diesel refill",
        }

        data.update(overrides)
        return data

    def create_fuel(self, **overrides):
        values = {
            "vehicle": self.vehicle,
            "fuel_type": "Diesel",
            "refill_date": self.refill_date,
            "litres": Decimal("100.00"),
            "price_per_litre": Decimal("2.50"),
            "fuel_station": "Penang Fuel Station",
            "mileage": 50000,
            "remarks": "Routine diesel refill",
        }

        values.update(overrides)
        return Fuel.objects.create(**values)

    # ==========================================
    # TC-F01: CREATE FUEL RECORD
    # ==========================================
    def test_owner_can_create_fuel(self):

        response = self.client.post(
            reverse("fuel:fuel_create"),
            self.fuel_data(),
        )

        self.assertRedirects(
            response,
            reverse("fuel:fuel_list"),
        )

        self.assertEqual(Fuel.objects.count(), 1)

        fuel = Fuel.objects.first()

        self.assertEqual(fuel.fuel_type, "Diesel")
        self.assertEqual(
            fuel.fuel_station,
            "Penang Fuel Station",
        )
        self.assertEqual(
            fuel.litres,
            Decimal("100.00"),
        )

        print("TC-F01: Fuel record created successfully")

    # ==========================================
    # TC-F02: UPDATE FUEL RECORD
    # ==========================================
    def test_owner_can_update_fuel(self):

        fuel = self.create_fuel()

        response = self.client.post(
            reverse(
                "fuel:fuel_update",
                args=[fuel.pk],
            ),
            self.fuel_data(
                fuel_type="Petrol",
                litres="80.00",
                price_per_litre="3.00",
                fuel_station="Updated Fuel Station",
                mileage=55000,
            ),
        )

        self.assertRedirects(
            response,
            reverse("fuel:fuel_list"),
        )

        fuel.refresh_from_db()

        self.assertEqual(fuel.fuel_type, "Petrol")
        self.assertEqual(
            fuel.fuel_station,
            "Updated Fuel Station",
        )
        self.assertEqual(
            fuel.litres,
            Decimal("80.00"),
        )
        self.assertEqual(
            fuel.total_cost,
            Decimal("240.00"),
        )

        print("TC-F02: Fuel record updated successfully")

    # ==========================================
    # TC-F03: DELETE FUEL RECORD
    # ==========================================
    def test_owner_can_delete_fuel(self):

        fuel = self.create_fuel()
        fuel_id = fuel.pk

        response = self.client.post(
            reverse(
                "fuel:fuel_delete",
                args=[fuel_id],
            ),
        )

        self.assertRedirects(
            response,
            reverse("fuel:fuel_list"),
        )

        self.assertFalse(
            Fuel.objects.filter(pk=fuel_id).exists()
        )

        print("TC-F03: Fuel record deleted successfully")

    # ==========================================
    # TC-F04: CUSTOMER ACCESS PROTECTION
    # ==========================================
    def test_customer_cannot_manage_fuel(self):

        fuel = self.create_fuel()

        self.client.force_login(self.customer)

        urls = [
            reverse("fuel:fuel_list"),
            reverse("fuel:fuel_create"),
            reverse("fuel:fuel_update", args=[fuel.pk]),
            reverse("fuel:fuel_delete", args=[fuel.pk]),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 403)

        # Customer cannot create
        response = self.client.post(
            reverse("fuel:fuel_create"),
            self.fuel_data(
                fuel_station="Unauthorized Station"
            ),
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Fuel.objects.count(), 1)

        # Customer cannot update
        response = self.client.post(
            reverse("fuel:fuel_update", args=[fuel.pk]),
            self.fuel_data(
                fuel_station="Unauthorized Update"
            ),
        )

        self.assertEqual(response.status_code, 403)

        fuel.refresh_from_db()

        self.assertEqual(
            fuel.fuel_station,
            "Penang Fuel Station",
        )

        # Customer cannot delete
        response = self.client.post(
            reverse("fuel:fuel_delete", args=[fuel.pk]),
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            Fuel.objects.filter(pk=fuel.pk).exists()
        )

        print("TC-F04: Customer access blocked successfully")

    # ==========================================
    # TC-F05: AUTOMATIC TOTAL COST
    # ==========================================
    def test_automatic_total_cost_calculation(self):

        fuel = self.create_fuel(
            litres=Decimal("120.00"),
            price_per_litre=Decimal("2.75"),
        )

        self.assertEqual(
            fuel.total_cost,
            Decimal("330.00"),
        )

        print("TC-F05: Total fuel cost calculated correctly")

    # ==========================================
    # TC-F06: REJECT NEGATIVE FUEL LITRES
    # ==========================================
    def test_rejects_negative_fuel_litres(self):

        response = self.client.post(
            reverse("fuel:fuel_create"),
            self.fuel_data(litres="-50.00"),
        )

        self.assertEqual(response.status_code, 200)

        self.assertIn(
            "litres",
            response.context["form"].errors,
        )

        self.assertEqual(Fuel.objects.count(), 0)

        print("TC-F06: Negative fuel litres rejected")

    # ==========================================
    # TC-F07: REJECT NEGATIVE FUEL PRICE
    # ==========================================
    def test_rejects_negative_fuel_price(self):

        response = self.client.post(
            reverse("fuel:fuel_create"),
            self.fuel_data(price_per_litre="-2.50"),
        )

        self.assertEqual(response.status_code, 200)

        self.assertIn(
            "price_per_litre",
            response.context["form"].errors,
        )

        self.assertEqual(Fuel.objects.count(), 0)

        print("TC-F07: Negative fuel price rejected")

    # ==========================================
    # TC-F08: SEARCH FUEL RECORDS
    # ==========================================
    def test_owner_can_search_fuel_records(self):

        matching = self.create_fuel(
            fuel_station="Penang Fuel Station"
        )

        self.create_fuel(
            fuel_station="Kuala Lumpur Fuel Station"
        )

        response = self.client.get(
            reverse("fuel:fuel_list"),
            {"search": "Penang"},
        )

        self.assertEqual(response.status_code, 200)

        results = list(
            response.context["page_obj"].object_list
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].pk, matching.pk)

        print("TC-F08: Fuel search successful")

    # ==========================================
    # TC-F09: VIEW FUEL RECORD LIST
    # ==========================================
    def test_owner_can_view_fuel_list(self):

        fuel = self.create_fuel()

        response = self.client.get(
            reverse("fuel:fuel_list")
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            fuel.fuel_station,
        )

        print("TC-F09: Fuel list displayed successfully")

    # ==========================================
    # TC-F10: GET REQUEST MUST NOT DELETE
    # ==========================================
    def test_get_request_does_not_delete_fuel(self):

        fuel = self.create_fuel()

        response = self.client.get(
            reverse(
                "fuel:fuel_delete",
                args=[fuel.pk],
            )
        )

        self.assertEqual(response.status_code, 200)

        self.assertTrue(
            Fuel.objects.filter(pk=fuel.pk).exists()
        )

        print("TC-F10: GET request did not delete fuel")

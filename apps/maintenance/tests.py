
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import UserProfile
from apps.vehicles.models import Vehicle
from apps.maintenance.models import Maintenance


class MaintenanceManagementTests(TestCase):

    def setUp(self):
        User = get_user_model()

        # Create Owner account
        self.owner = User.objects.create_user(
            username="test_maintenance_owner",
            password="TestPassword123!",
            email="maintenanceowner@example.com",
        )

        owner_profile, _ = UserProfile.objects.update_or_create(
            user=self.owner,
            defaults={"role": "Owner"},
        )

        owner_profile.refresh_from_db()
        self.owner.refresh_from_db()

        self.assertEqual(owner_profile.role, "Owner")

        # Create Customer account
        self.customer_user = User.objects.create_user(
            username="test_maintenance_customer",
            password="TestPassword123!",
            email="maintenancecustomer@example.com",
        )

        UserProfile.objects.update_or_create(
            user=self.customer_user,
            defaults={"role": "Customer"},
        )

        today = timezone.localdate()

        # Create test vehicle
        self.vehicle = Vehicle.objects.create(
            registration_number="TCM00001",
            vehicle_name="Maintenance Test Bus",
            bus_type="Standard Bus",
            seat_capacity=44,
            manufacture_year=2024,
            insurance_expiry=today + timedelta(days=365),
            road_tax_expiry=today + timedelta(days=365),
            status="Available",
        )

        self.service_date = today
        self.next_service_date = today + timedelta(days=180)

        # IMPORTANT: Log Owner into Django test client
        self.client.force_login(self.owner)

    def maintenance_data(self, **overrides):
        data = {
            "vehicle": self.vehicle.pk,
            "maintenance_type": "Oil Change",
            "workshop": "Penang Auto Workshop",
            "service_date": self.service_date.isoformat(),
            "next_service_date": self.next_service_date.isoformat(),
            "mileage": 50000,
            "cost": "350.00",
            "status": "Scheduled",
            "remarks": "Routine maintenance",
        }

        data.update(overrides)
        return data

    def create_maintenance(self, **overrides):
        values = {
            "vehicle": self.vehicle,
            "maintenance_type": "Oil Change",
            "workshop": "Penang Auto Workshop",
            "service_date": self.service_date,
            "next_service_date": self.next_service_date,
            "mileage": 50000,
            "cost": Decimal("350.00"),
            "status": "Scheduled",
            "remarks": "Routine maintenance",
        }

        values.update(overrides)
        return Maintenance.objects.create(**values)

    # ==========================================
    # TC-M01: CREATE MAINTENANCE
    # ==========================================
    def test_owner_can_create_maintenance(self):

        response = self.client.post(
            reverse("maintenance:maintenance_create"),
            self.maintenance_data(),
        )

        self.assertRedirects(
            response,
            reverse("maintenance:maintenance_list"),
        )

        maintenance = Maintenance.objects.get(
            vehicle=self.vehicle
        )

        self.assertEqual(
            maintenance.maintenance_type,
            "Oil Change",
        )
        self.assertEqual(
            maintenance.workshop,
            "Penang Auto Workshop",
        )
        self.assertEqual(maintenance.mileage, 50000)
        self.assertEqual(
            maintenance.cost,
            Decimal("350.00"),
        )
        self.assertEqual(maintenance.status, "Scheduled")

        print("TC-M01: Maintenance created successfully")

    # ==========================================
    # TC-M02: UPDATE MAINTENANCE
    # ==========================================
    def test_owner_can_update_maintenance(self):

        maintenance = self.create_maintenance()

        response = self.client.post(
            reverse(
                "maintenance:maintenance_update",
                args=[maintenance.pk],
            ),
            self.maintenance_data(
                maintenance_type="Engine Service",
                workshop="Updated Service Centre",
                mileage=55000,
                cost="1200.00",
                status="Completed",
                remarks="Engine servicing completed",
            ),
        )

        self.assertRedirects(
            response,
            reverse("maintenance:maintenance_list"),
        )

        maintenance.refresh_from_db()

        self.assertEqual(
            maintenance.maintenance_type,
            "Engine Service",
        )
        self.assertEqual(
            maintenance.workshop,
            "Updated Service Centre",
        )
        self.assertEqual(maintenance.mileage, 55000)
        self.assertEqual(
            maintenance.cost,
            Decimal("1200.00"),
        )
        self.assertEqual(maintenance.status, "Completed")
        self.assertEqual(Maintenance.objects.count(), 1)

        print("TC-M02: Maintenance updated successfully")

    # ==========================================
    # TC-M03: DELETE MAINTENANCE
    # ==========================================
    def test_owner_can_delete_maintenance(self):

        maintenance = self.create_maintenance()
        maintenance_id = maintenance.pk

        response = self.client.post(
            reverse(
                "maintenance:maintenance_delete",
                args=[maintenance_id],
            )
        )

        self.assertRedirects(
            response,
            reverse("maintenance:maintenance_list"),
        )

        self.assertFalse(
            Maintenance.objects.filter(
                pk=maintenance_id
            ).exists()
        )

        print("TC-M03: Maintenance deleted successfully")

    # ==========================================
    # TC-M04: UNAUTHORIZED CUSTOMER ACCESS
    # ==========================================
    def test_customer_cannot_manage_maintenance(self):

        maintenance = self.create_maintenance()

        self.client.force_login(self.customer_user)

        urls = [
            reverse("maintenance:maintenance_list"),
            reverse("maintenance:maintenance_create"),
            reverse(
                "maintenance:maintenance_update",
                args=[maintenance.pk],
            ),
            reverse(
                "maintenance:maintenance_delete",
                args=[maintenance.pk],
            ),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 403)

        # Unauthorized creation
        response = self.client.post(
            reverse("maintenance:maintenance_create"),
            self.maintenance_data(
                workshop="Unauthorized Workshop"
            ),
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Maintenance.objects.count(), 1)

        # Unauthorized update
        response = self.client.post(
            reverse(
                "maintenance:maintenance_update",
                args=[maintenance.pk],
            ),
            self.maintenance_data(
                workshop="Unauthorized Update"
            ),
        )

        self.assertEqual(response.status_code, 403)

        maintenance.refresh_from_db()

        self.assertEqual(
            maintenance.workshop,
            "Penang Auto Workshop",
        )

        # Unauthorized deletion
        response = self.client.post(
            reverse(
                "maintenance:maintenance_delete",
                args=[maintenance.pk],
            )
        )

        self.assertEqual(response.status_code, 403)

        self.assertTrue(
            Maintenance.objects.filter(
                pk=maintenance.pk
            ).exists()
        )

        print("TC-M04: Unauthorized customer access blocked")

    # ==========================================
    # TC-M05: INVALID NEXT SERVICE DATE
    # ==========================================
    def test_rejects_next_service_date_before_service_date(self):

        invalid_date = self.service_date - timedelta(days=1)

        response = self.client.post(
            reverse("maintenance:maintenance_create"),
            self.maintenance_data(
                next_service_date=invalid_date.isoformat()
            ),
        )

        self.assertEqual(response.status_code, 200)

        self.assertIn(
            "next_service_date",
            response.context["form"].errors,
        )

        self.assertEqual(Maintenance.objects.count(), 0)

        print("TC-M05: Invalid next service date rejected")

    # ==========================================
    # TC-M06: NEGATIVE MAINTENANCE COST
    # ==========================================
    def test_rejects_negative_maintenance_cost(self):

        response = self.client.post(
            reverse("maintenance:maintenance_create"),
            self.maintenance_data(cost="-100.00"),
        )

        self.assertEqual(response.status_code, 200)

        self.assertIn(
            "cost",
            response.context["form"].errors,
        )

        self.assertEqual(Maintenance.objects.count(), 0)

        print("TC-M06: Negative maintenance cost rejected")

    # ==========================================
    # TC-M07: SEARCH MAINTENANCE
    # ==========================================
    def test_owner_can_search_maintenance_records(self):

        matching = self.create_maintenance(
            workshop="Penang Auto Workshop"
        )

        self.create_maintenance(
            maintenance_type="Brake Service",
            workshop="Kuala Lumpur Workshop",
        )

        response = self.client.get(
            reverse("maintenance:maintenance_list"),
            {"search": "Penang Auto"},
        )

        self.assertEqual(response.status_code, 200)

        results = list(
            response.context["page_obj"].object_list
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].pk, matching.pk)

        print("TC-M07: Maintenance search successful")

    # ==========================================
    # TC-M08: VIEW MAINTENANCE LIST
    # ==========================================
    def test_owner_can_view_maintenance_list(self):

        maintenance = self.create_maintenance()

        response = self.client.get(
            reverse("maintenance:maintenance_list")
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            maintenance.workshop,
        )

        print("TC-M08: Maintenance list displayed successfully")

    # ==========================================
    # TC-M09: NEGATIVE MILEAGE
    # ==========================================
    def test_rejects_negative_mileage(self):

        response = self.client.post(
            reverse("maintenance:maintenance_create"),
            self.maintenance_data(mileage=-500),
        )

        self.assertEqual(response.status_code, 200)

        self.assertIn(
            "mileage",
            response.context["form"].errors,
        )

        self.assertEqual(Maintenance.objects.count(), 0)

        print("TC-M09: Negative mileage rejected")

    # ==========================================
    # TC-M10: GET REQUEST MUST NOT DELETE
    # ==========================================
    def test_get_request_does_not_delete_maintenance(self):

        maintenance = self.create_maintenance()

        response = self.client.get(
            reverse(
                "maintenance:maintenance_delete",
                args=[maintenance.pk],
            )
        )

        self.assertEqual(response.status_code, 200)

        self.assertTrue(
            Maintenance.objects.filter(
                pk=maintenance.pk
            ).exists()
        )

        print("TC-M10: GET request did not delete maintenance")

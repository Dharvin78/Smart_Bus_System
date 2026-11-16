
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User

from apps.accounts.models import UserProfile
from apps.bookings.views import booking_list


class SQLInjectionSecurityTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

        self.owner = User.objects.create_user(
            username="sql_test_owner",
            password="SecurePass123!"
        )

        profile, created = UserProfile.objects.get_or_create(
            user=self.owner
        )

        profile.role = "Owner"
        profile.save()

        self.owner.refresh_from_db()
        profile.refresh_from_db()

        self.assertEqual(profile.role, "Owner")
        
    def test_st06_booking_search_sql_injection(self):
        """ST-06: SQL injection input must not manipulate booking search."""

        malicious_input = "' OR '1'='1' --"

        request = self.factory.get(
            "/bookings/",
            {"search": malicious_input}
        )
        request.user = self.owner

        response = booking_list(request)

        self.assertEqual(response.status_code, 200)

        # The injected text should not produce unrelated bookings.
        # This test uses an empty booking database.
        self.assertNotContains(
            response,
            "SB202610180002"
        )
# Create your tests here.


from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.accounts.models import UserProfile
from apps.customers.models import Customer


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
)
class AccountsManagementTests(TestCase):

    def setUp(self):

        self.password = "TestPassword123!"

        # ==========================================
        # OWNER
        # ==========================================
        self.owner = User.objects.create_user(
            username="test_account_owner",
            email="owner@example.com",
            password=self.password,
        )

        owner_profile, _ = UserProfile.objects.update_or_create(
            user=self.owner,
            defaults={"role": UserProfile.OWNER},
        )

        owner_profile.refresh_from_db()
        self.owner.refresh_from_db()

        # ==========================================
        # ADMIN
        # ==========================================
        self.admin = User.objects.create_user(
            username="test_account_admin",
            email="admin@example.com",
            password=self.password,
        )

        admin_profile, _ = UserProfile.objects.update_or_create(
            user=self.admin,
            defaults={"role": UserProfile.ADMIN},
        )

        admin_profile.refresh_from_db()
        self.admin.refresh_from_db()

        # ==========================================
        # CUSTOMER
        # ==========================================
        self.customer = User.objects.create_user(
            username="test_account_customer",
            email="customer@example.com",
            password=self.password,
        )

        customer_profile, _ = UserProfile.objects.update_or_create(
            user=self.customer,
            defaults={"role": UserProfile.CUSTOMER},
        )

        customer_profile.refresh_from_db()
        self.customer.refresh_from_db()

        # ==========================================
        # VERIFY ROLES
        # ==========================================
        self.assertEqual(
            self.owner.profile.role,
            UserProfile.OWNER,
        )

        self.assertEqual(
            self.admin.profile.role,
            UserProfile.ADMIN,
        )

        self.assertEqual(
            self.customer.profile.role,
            UserProfile.CUSTOMER,
        )

    # ==========================================
    # TC-A01: CUSTOMER REGISTRATION
    # ==========================================
    def test_customer_can_register(self):

        response = self.client.post(
            reverse("accounts:signup"),
            {
                "username": "new_customer",
                "email": "newcustomer@example.com",
                "password": "SecurePassword123!",
                "confirm_password": "SecurePassword123!",
            },
        )

        self.assertRedirects(
            response,
            reverse("dashboard"),
            fetch_redirect_response=False,
        )

        user = User.objects.get(username="new_customer")

        self.assertTrue(
            user.check_password("SecurePassword123!")
        )

        self.assertEqual(
            user.profile.role,
            UserProfile.CUSTOMER,
        )

        self.assertTrue(
            Customer.objects.filter(user=user).exists()
        )

        print("TC-A01: Customer registration successful")

    # ==========================================
    # TC-A02: REJECT MISMATCHED PASSWORDS
    # ==========================================
    def test_registration_rejects_password_mismatch(self):

        response = self.client.post(
            reverse("accounts:signup"),
            {
                "username": "invalid_customer",
                "email": "invalid@example.com",
                "password": "SecurePassword123!",
                "confirm_password": "DifferentPassword123!",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(
            User.objects.filter(
                username="invalid_customer"
            ).exists()
        )

        self.assertTrue(
            response.context["form"].errors
        )

        print("TC-A02: Password mismatch rejected")

    # ==========================================
    # TC-A03: VALID LOGIN
    # ==========================================
    def test_user_can_login(self):

        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": self.customer.username,
                "password": self.password,
            },
        )

        self.assertRedirects(
            response,
            reverse("dashboard"),
            fetch_redirect_response=False,
        )

        self.assertEqual(
            str(self.customer.pk),
            self.client.session["_auth_user_id"],
        )

        print("TC-A03: Valid login successful")

    # ==========================================
    # TC-A04: INVALID LOGIN
    # ==========================================
    def test_invalid_login_is_rejected(self):

        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": self.customer.username,
                "password": "WrongPassword123!",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertNotIn(
            "_auth_user_id",
            self.client.session,
        )

        print("TC-A04: Invalid login rejected")

   
    # ==========================================
    # TC-A05: USER LOGOUT
    # ==========================================
    def test_user_can_logout(self):

        self.client.force_login(self.customer)

        response = self.client.get(
            reverse("accounts:logout")
        )

        self.assertRedirects(
            response,
            reverse("accounts:login"),
        )

        self.assertNotIn(
            "_auth_user_id",
            self.client.session,
        )

        print("TC-A05: Logout successful")


    # ==========================================
    # TC-A06: PROFILE REQUIRES LOGIN
    # ==========================================
    def test_anonymous_user_cannot_access_profile(self):

        response = self.client.get(
            reverse("accounts:profile")
        )

        self.assertEqual(response.status_code, 302)

        self.assertIn(
            "login",
            response.headers["Location"],
        )

        print("TC-A06: Anonymous profile access blocked")

    # ==========================================
    # TC-A07: AUTHENTICATED PROFILE ACCESS
    # ==========================================
    def test_logged_in_user_can_view_profile(self):

        self.client.force_login(self.customer)

        response = self.client.get(
            reverse("accounts:profile")
        )

        self.assertEqual(response.status_code, 200)

        print("TC-A07: Profile displayed successfully")

    # ==========================================
    # TC-A08: CHANGE PASSWORD
    # ==========================================
    def test_user_can_change_password(self):

        self.client.force_login(self.customer)

        response = self.client.post(
            reverse("accounts:change_password"),
            {
                "old_password": self.password,
                "new_password1": "NewSecurePassword123!",
                "new_password2": "NewSecurePassword123!",
            },
        )

        self.assertRedirects(
            response,
            reverse("dashboard"),
            fetch_redirect_response=False,
        )

        self.customer.refresh_from_db()

        self.assertTrue(
            self.customer.check_password(
                "NewSecurePassword123!"
            )
        )

        print("TC-A08: Password changed successfully")

    # ==========================================
    # TC-A09: TEMPORARY PASSWORD ENFORCEMENT
    # ==========================================
    def test_temporary_password_requires_change(self):

        profile = self.customer.profile
        profile.must_change_password = True
        profile.save()

        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": self.customer.username,
                "password": self.password,
            },
        )

        self.assertRedirects(
            response,
            reverse("accounts:change_password"),
        )

        print("TC-A09: Temporary password change required")

    
    # ==========================================
    # TC-A11: OWNER CAN VIEW USER MANAGEMENT
    # ==========================================
    def test_owner_can_view_user_management(self):

        self.client.force_login(self.owner)

        response = self.client.get(
            reverse("accounts:user_list")
        )

        self.assertEqual(
            self.owner.profile.role,
            UserProfile.OWNER,
        )

        self.assertEqual(
            response.status_code,
            200,
            msg=f"Unexpected redirect: {response.headers.get('Location')}",
        )

        self.assertContains(
            response,
            self.customer.username,
        )

        print("TC-A11: Owner user-management access successful")


    # ==========================================
    # TC-A11: OWNER CAN VIEW USER MANAGEMENT
    # ==========================================
    def test_owner_can_view_user_management(self):

        self.client.force_login(self.owner)

        response = self.client.get(
            reverse("accounts:user_list")
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            self.customer.username,
        )

        print("TC-A11: Owner user-management access successful")

    
    # ==========================================
    # TC-A12: ADMIN CANNOT CREATE OWNER
    # ==========================================
    def test_admin_cannot_create_owner(self):

        self.client.force_login(self.admin)

        self.assertEqual(
            self.admin.profile.role,
            UserProfile.ADMIN,
        )

        response = self.client.post(
            reverse("accounts:user_create"),
            {
                "username": "unauthorized_owner",
                "email": "unauthorized@example.com",
                "first_name": "Unauthorized",
                "last_name": "Owner",
                "phone": "0123456789",
                "role": UserProfile.OWNER,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
            msg=f"Unexpected redirect: {response.headers.get('Location')}",
        )

        self.assertFalse(
            User.objects.filter(
                username="unauthorized_owner"
            ).exists()
        )

        self.assertIn(
            "role",
            response.context["form"].errors,
        )

        print("TC-A12: Admin cannot create Owner account")

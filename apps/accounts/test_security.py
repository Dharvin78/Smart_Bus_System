from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.contrib.auth import SESSION_KEY
from django.urls import reverse

from datetime import timedelta, time
from decimal import Decimal
from unittest.mock import patch
from django.utils import timezone

from apps.accounts.models import UserProfile
from apps.customers.models import Customer
from apps.bookings.models import Booking
from apps.payments.models import Payment

class SecurityTests(TestCase):

    def test_password_is_hashed(self):
        """
        ST-01: Verify that user passwords are securely hashed
        instead of being stored as plaintext.
        """

        # Create a test user
        original_password = "SecurePassword123!"

        user = User.objects.create_user(
            username="security_test_user",
            email="security@example.com",
            password=original_password
        )

        # Retrieve the saved user from database
        saved_user = User.objects.get(
            username="security_test_user"
        )

        # Ensure password is not stored as plaintext
        self.assertNotEqual(
            saved_user.password,
            original_password
        )

        # Verify Django recognizes the password hash
        self.assertTrue(
            saved_user.check_password(original_password)
        )

        # Verify incorrect passwords are rejected
        self.assertFalse(
            saved_user.check_password("WrongPassword123!")
        )

        print("TC-ST01: Password hashing security verified")
        print("Result: Password is not stored in plaintext")
        print("Result: Correct password verified successfully")
        print("Result: Incorrect password rejected")

    def test_csrf_protection(self):
        """
        ST-02: Verify that Django rejects POST requests
        without a valid CSRF token.
        """

        # Create a client that enforces CSRF checks
        csrf_client = Client(enforce_csrf_checks=True)

        # Submit login form without CSRF token
        response = csrf_client.post(
            reverse("accounts:login"),
            {
                "username": "security_test_user",
                "password": "SecurePassword123!"
            }
        )

        # Verify request is rejected
        self.assertEqual(response.status_code, 403)

        # Verify no user was authenticated
        self.assertNotIn(
            "_auth_user_id",
            csrf_client.session
        )

        print("TC-ST02: CSRF protection verified")
        print("HTTP Status:", response.status_code)
        print("Result: POST request without CSRF token rejected")


    def test_session_security_after_logout(self):
        # Create a test user
        User.objects.create_user(
            username="security_test_user",
            email="security@example.com",
            password="SecurePassword123!"
        )

        # Log in with the test account
        login_success = self.client.login(
            username="security_test_user",
            password="SecurePassword123!"
        )

        self.assertTrue(login_success)

        # Verify authenticated session exists
        self.assertIn(
            SESSION_KEY,
            self.client.session
        )

        print("Step 1: User login successful")
        print("Step 2: Authenticated session created")

        # Log out using Django's test client
        self.client.logout()

        # Verify session is invalidated
        self.assertNotIn(
            SESSION_KEY,
            self.client.session
        )

        # Verify subsequent requests are anonymous
        response = self.client.get("/")

        self.assertFalse(
            response.wsgi_request.user.is_authenticated
        )

        print("Step 3: User logged out")
        print("Step 4: Authenticated session invalidated")
        print("Step 5: Subsequent request is anonymous")
        print("TC-ST03: Session security verified")


    def test_unauthorized_payment_access(self):
        """
        ST-04: Verify that Customer B cannot access
        Customer A's payment receipt.
        """
        # Create two users
        user_a = User.objects.create_user(
            username="customer_a_security",
            password="SecurePassword123!"
        )

        user_b = User.objects.create_user(
            username="customer_b_security",
            password="SecurePassword123!"
        )

        # Assign Customer role to both users
        # update_or_create handles projects where a
        # UserProfile is automatically created by signals.
        UserProfile.objects.update_or_create(
            user=user_a,
            defaults={"role": "Customer"}
        )

        UserProfile.objects.update_or_create(
            user=user_b,
            defaults={"role": "Customer"}
        )

        # Create Customer records
        customer_a = Customer.objects.create(
            user=user_a,
            first_name="Customer",
            last_name="A",
            email="customer_a@example.com",
            phone="0111111111",
            address="Test Address A",
            city="Penang",
            state="Penang",
            postcode="14000",
            gender="Male"
        )

        customer_b = Customer.objects.create(
            user=user_b,
            first_name="Customer",
            last_name="B",
            email="customer_b@example.com",
            phone="0122222222",
            address="Test Address B",
            city="Penang",
            state="Penang",
            postcode="14000",
            gender="Female"
        )

        # Create a booking for Customer A
        booking_a = Booking.objects.create(
            customer=customer_a,
            pickup_location="Bukit Mertajam",
            destination="George Town",
            travel_date=(
                timezone.localdate() + timedelta(days=7)
            ),
            departure_time=time(9, 0),
            passenger_count=10,
            total_price=Decimal("1000.00"),
            booking_status="Confirmed",
            payment_status="Paid"
        )

        # Create a payment for Customer A
        payment_a = Payment.objects.create(
            booking=booking_a,
            amount=Decimal("1000.00"),
            payment_method="Online Banking",
            payment_status="Paid",
            payment_date=timezone.localdate(),
            transaction_id="ST04-TEST-001"
        )

        receipt_url = reverse(
            "payments:payment_receipt",
            args=[payment_a.pk]
        )

        # Verify Customer A can access their own payment receipt.
        self.client.force_login(user_a)

        # Mock PDF generation so this test focuses
        # on receipt access authorization.
        from io import BytesIO

        with patch(
            "apps.payments.views.generate_payment_receipt",
            return_value=BytesIO(b"%PDF-1.4 test receipt")
        ):
            response_a = self.client.get(receipt_url)

        self.assertEqual(response_a.status_code, 200)

        print("Step 1: Customer A accessed own receipt")
        print("Customer A HTTP Status:", response_a.status_code)

        # Log in as Customer B
        self.client.logout()
        self.client.force_login(user_b)

        # Customer B attempts to access, Customer A's receipt.
        response_b = self.client.get(receipt_url)

        # Verify access is denied
        self.assertEqual(response_b.status_code, 404)

        print("Step 2: Customer B attempted unauthorized access")
        print("Customer B HTTP Status:", response_b.status_code)
        print("Result: Unauthorized payment access blocked")
        print("TC-ST04: Payment access security verified")


    def test_xss_protection(self):
        """
        ST-05: Verify Django automatically escapes
        potentially unsafe HTML in template output.
        """

        from django.template import Context, Template

        # Prepare harmless XSS test input
        malicious_input = (
            '<script>alert("XSS Test")</script>'
        )

        # Render the input using Django template
        template = Template(
            "<div>{{ user_input }}</div>"
        )

        rendered_output = template.render(
            Context({
                "user_input": malicious_input
            })
        )

        # Verify script tags are not rendered
        # as executable HTML
        self.assertNotIn(
            "<script>",
            rendered_output
        )

        self.assertNotIn(
            "</script>",
            rendered_output
        )

        # Verify HTML characters are escaped
        self.assertIn(
            "&lt;script&gt;",
            rendered_output
        )

        self.assertIn(
            "&lt;/script&gt;",
            rendered_output
        )

        print("Step 1: XSS test input submitted")
        print("Step 2: Template rendered successfully")
        print("Step 3: Script tags escaped")
        print("Rendered Output:", rendered_output)
        print("TC-ST05: XSS template protection verified")


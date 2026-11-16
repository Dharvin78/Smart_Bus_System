
from decimal import Decimal

from django import forms
from django.test import SimpleTestCase

from apps.bookings.forms import (
    CustomerBookingForm,
    BookingReviewForm,
)


class BookingUnitTesting(SimpleTestCase):

    def validate_passenger_count(self, count):
        """
        Execute the existing passenger validation method
        with a specified cleaned value.
        """
        form = CustomerBookingForm()
        form.cleaned_data = {"passenger_count": count}

        return form.clean_passenger_count()

    def validate_booking_price(self, value):
        """
        Execute the existing total_price field validation
        without creating a booking or using the database.
        """
        field = BookingReviewForm.base_fields["total_price"]
        return field.clean(value)

    def test_ut01_valid_passenger_count(self):
        """UT-01: Accept a valid passenger count."""

        result = self.validate_passenger_count(30)

        self.assertEqual(result, 30)

    def test_ut02_exceed_passenger_limit(self):
        """UT-02: Reject passenger count above 42."""

        with self.assertRaises(forms.ValidationError):
            self.validate_passenger_count(43)

    def test_ut03_zero_passengers(self):
        """UT-03: Reject zero passengers."""

        with self.assertRaises(forms.ValidationError):
            self.validate_passenger_count(0)

    def test_ut04_valid_booking_price(self):
        """UT-04: Accept a valid booking price."""

        result = self.validate_booking_price("1500.00")

        self.assertEqual(result, Decimal("1500.00"))

    def test_ut05_invalid_booking_price(self):
        """UT-05: Reject a negative booking price."""

        with self.assertRaises(forms.ValidationError):
            self.validate_booking_price("-100.00")

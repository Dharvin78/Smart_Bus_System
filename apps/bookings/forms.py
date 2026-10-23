from django import forms
from .models import Booking
from decimal import Decimal

class BookingForm(forms.ModelForm):

    class Meta:

        model = Booking

        fields = [
            "customer",
            "vehicle",
            "driver",
            "pickup_location",
            "destination",
            "travel_date",
            "departure_time",
            "return_date",
            "passenger_count",
            "total_price",
            "booking_status",
            "payment_status",
            "remarks",
        ]

        widgets = {

            "customer": forms.Select(attrs={
                "class": "form-select"
            }),

            "vehicle": forms.Select(attrs={
                "class": "form-select"
            }),

            "driver": forms.Select(attrs={
                "class": "form-select"
            }),

            "pickup_location": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Pickup Location"
            }),

            "destination": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Destination"
            }),

            "travel_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),

            "departure_time": forms.TimeInput(attrs={
                "class": "form-control",
                "type": "time"
            }),

            "return_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),

            "passenger_count": forms.NumberInput(attrs={
                "class": "form-control"
            }),

            "total_price": forms.NumberInput(attrs={
                "class": "form-control"
            }),

            "booking_status": forms.Select(attrs={
                "class": "form-select"
            }),

            "payment_status": forms.Select(attrs={
                "class": "form-select"
            }),

            "remarks": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3
            }),

        }


class BookingReviewForm(forms.Form):

    vehicle = forms.ModelChoiceField(
        queryset=None,
        required=True,
        empty_label="Select Vehicle",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    driver = forms.ModelChoiceField(
        queryset=None,
        required=True,
        empty_label="Select Driver",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    total_price = forms.DecimalField(
        required=True,
        min_value=Decimal("0.01"),
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "min": "0.01",
            "step": "0.01",
            "placeholder": "Enter booking price",
        }),
    )

    approval_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 3,
            "placeholder": "Enter optional approval notes...",
        }),
    )

    def __init__(self, *args, **kwargs):
        vehicle_queryset = kwargs.pop("vehicle_queryset", None)
        driver_queryset = kwargs.pop("driver_queryset", None)

        super().__init__(*args, **kwargs)

        from apps.vehicles.models import Vehicle
        from apps.drivers.models import Driver

        self.fields["vehicle"].queryset = (
            vehicle_queryset
            if vehicle_queryset is not None
            else Vehicle.objects.filter(status="Available")
        )

        self.fields["driver"].queryset = (
            driver_queryset
            if driver_queryset is not None
            else Driver.objects.filter(status="Available")
        )

class BookingRejectForm(forms.Form):

    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 3,
            "placeholder": "Enter optional rejection notes...",
        }),
    )

class CustomerBookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = [
            "pickup_location",
            "destination",
            "travel_date",
            "departure_time",
            "return_date",
            "passenger_count",
            "remarks",
        ]

        widgets = {
            "pickup_location": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Pickup Location",
            }),
            "destination": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Destination",
            }),
            "travel_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "departure_time": forms.TimeInput(attrs={
                "class": "form-control",
                "type": "time",
            }),
            "return_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "passenger_count": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 1,
                "max": 42,
            }),
            "remarks": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Additional requirements (optional)",
            }),
        }

    def clean_passenger_count(self):
        count = self.cleaned_data["passenger_count"]

        if count < 1 or count > 42:
            raise forms.ValidationError(
                "Passenger count must be between 1 and 42."
            )

        return count
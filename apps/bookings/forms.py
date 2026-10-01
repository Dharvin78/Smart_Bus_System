from django import forms

from .models import Booking


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
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
        empty_label="Select Vehicle",
    )

    driver = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
        empty_label="Select Driver",
    )

    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Enter the reason if rejecting this booking...",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        vehicle_queryset = kwargs.pop("vehicle_queryset")
        driver_queryset = kwargs.pop("driver_queryset")

        super().__init__(*args, **kwargs)

        self.fields["vehicle"].queryset = vehicle_queryset
        self.fields["driver"].queryset = driver_queryset
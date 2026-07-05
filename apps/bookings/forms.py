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
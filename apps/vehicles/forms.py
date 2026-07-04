from django import forms
from .models import Vehicle


class VehicleForm(forms.ModelForm):

    class Meta:
        model = Vehicle

        fields = [
            "registration_number",
            "vehicle_name",
            "bus_type",
            "seat_capacity",
            "manufacture_year",
            "insurance_expiry",
            "road_tax_expiry",
            "status",
            "image",
        ]

        widgets = {
            "registration_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Registration Number"
            }),

            "vehicle_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Vehicle Name"
            }),

            "bus_type": forms.Select(attrs={
                "class": "form-select"
            }),

            "seat_capacity": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "1"
            }),

            "manufacture_year": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Manufacture Year"
            }),

            "insurance_expiry": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),

            "road_tax_expiry": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),

            "status": forms.Select(attrs={
                "class": "form-select"
            }),

            "image": forms.ClearableFileInput(attrs={
                "class": "form-control"
            }),
        }
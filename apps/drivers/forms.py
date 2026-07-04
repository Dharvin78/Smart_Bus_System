from django import forms
from .models import Driver


class DriverForm(forms.ModelForm):

    class Meta:
        model = Driver

        fields = [
            "full_name",
            "ic_passport",
            "phone",
            "email",
            "address",
            "driving_license",
            "license_expiry",
            "assigned_vehicle",
            "status",
            "photo",
        ]

        widgets = {

            "full_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Driver Full Name"
            }),

            "ic_passport": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "IC / Passport Number"
            }),

            "phone": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Phone Number"
            }),

            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "Email Address"
            }),

            "address": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Home Address"
            }),

            "driving_license": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Driving License Number"
            }),

            "license_expiry": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),

            "assigned_vehicle": forms.Select(attrs={
                "class": "form-select"
            }),

            "status": forms.Select(attrs={
                "class": "form-select"
            }),

            "photo": forms.ClearableFileInput(attrs={
                "class": "form-control"
            }),
        }
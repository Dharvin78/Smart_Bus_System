from django import forms
from .models import Driver, DriverReview


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

class DriverReviewForm(forms.ModelForm):

    class Meta:
        model = DriverReview

        fields = [
            "rating",
            "comment",
        ]

        widgets = {

            "rating": forms.RadioSelect(
                choices=[
                    (1, "1"),
                    (2, "2"),
                    (3, "3"),
                    (4, "4"),
                    (5, "5"),
                ],
                attrs={
                    "class": "rating-input"
                }
            ),

            "comment": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Tell us about your experience with the driver..."
            }),
        }

        labels = {
            "rating": "Driver Rating",
            "comment": "Comment",
        }
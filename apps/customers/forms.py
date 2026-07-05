from django import forms
from .models import Customer


class CustomerForm(forms.ModelForm):

    class Meta:

        model = Customer

        fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "address",
            "city",
            "state",
            "postcode",
            "gender",
            "profile_picture",
        ]

        widgets = {

            "first_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "First Name",
            }),

            "last_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Last Name",
            }),

            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "Email Address",
            }),

            "phone": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Phone Number",
            }),

            "address": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
            }),

            "city": forms.TextInput(attrs={
                "class": "form-control",
            }),

            "state": forms.TextInput(attrs={
                "class": "form-control",
            }),

            "postcode": forms.TextInput(attrs={
                "class": "form-control",
            }),

            "gender": forms.Select(attrs={
                "class": "form-select",
            }),

            "profile_picture": forms.ClearableFileInput(attrs={
                "class": "form-control",
            }),

        }
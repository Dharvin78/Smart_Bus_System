from django import forms

from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm

from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from .decorators import role_required
from .models import UserProfile


class SignupForm(forms.ModelForm):

    password = forms.CharField(
        widget=forms.PasswordInput()
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput()
    )

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password'
        ]

    def clean(self):

        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm_password")

        if password != confirm:
            raise forms.ValidationError("Passwords do not match.")

        return cleaned_data

class ProfileForm(forms.ModelForm):

    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter first name"
        })
    )

    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter last name"
        })
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "Enter email address"
        })
    )

    class Meta:
        model = UserProfile

        fields = [
            "profile_picture",
            "phone",
            "gender",
            "address",
            "city",
            "state",
            "postcode",
        ]

        widgets = {

            "profile_picture": forms.FileInput(attrs={
                "class": "form-control",
                "accept": "image/*",
                "id": "profilePictureInput",
            }),

            "phone": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter phone number"
            }),

            "gender": forms.Select(attrs={
                "class": "form-select"
            }),

            "address": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Enter your address"
            }),

            "city": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter city"
            }),

            "state": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter state"
            }),

            "postcode": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter postcode"
            }),
        }

    def __init__(self, *args, **kwargs):

        self.profile = kwargs.pop("profile", None)
        self.current_role = kwargs.pop("current_role", None)

        super().__init__(*args, **kwargs)

        if self.profile:
            self.fields["role"].initial = self.profile.role
            self.fields["phone"].initial = self.profile.phone

        if self.current_role == UserProfile.ADMIN:
            self.fields["role"].choices = [
                (UserProfile.DRIVER, "Driver"),
                (UserProfile.CUSTOMER, "Customer"),
            ]

    def save(self, user, commit=True):

        profile = super().save(commit=False)

        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]

        if commit:
            user.save()
            profile.save()

        return profile

class CustomPasswordChangeForm(PasswordChangeForm):

    old_password = forms.CharField(
        label="Current Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter current password"
            }
        )
    )

    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter new password"
            }
        )
    )

    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirm new password"
            }
        )
    )
# Manage User Form
class ManageUserForm(forms.ModelForm):
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"})
    )

    first_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter first name"
        })
    )

    last_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter last name"
        })
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "Enter email address"
        })
    )

    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter phone number"
        })
    )

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name"]

        widgets = {
            "username": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter username"
            })
        }

    def __init__(self, *args, **kwargs):
        self.profile = kwargs.pop("profile", None)
        self.requesting_user = kwargs.pop("user", None)

        super().__init__(*args, **kwargs)

        if self.profile:
            self.fields["role"].initial = self.profile.role
            self.fields["phone"].initial = self.profile.phone

        # Admin can only create/manage Drivers and Customers
        if (
            self.requesting_user
            and hasattr(self.requesting_user, "profile")
            and self.requesting_user.profile.role == UserProfile.ADMIN
        ):
            self.fields["role"].choices = [
                (UserProfile.DRIVER, "Driver"),
                (UserProfile.CUSTOMER, "Customer"),
            ]

    def clean_role(self):
        role = self.cleaned_data["role"]

        if (
            self.requesting_user
            and hasattr(self.requesting_user, "profile")
            and self.requesting_user.profile.role == UserProfile.ADMIN
        ):
            if role not in [UserProfile.DRIVER, UserProfile.CUSTOMER]:
                raise forms.ValidationError(
                    "Admins can only manage Drivers and Customers."
                )

        return role

    def save(self, commit=True):
        user = super().save(commit=False)

        if commit:
            user.save()

            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    "role": self.cleaned_data["role"],
                    "phone": self.cleaned_data["phone"],
                }
            )

        return user
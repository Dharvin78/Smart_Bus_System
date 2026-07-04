# Create your models here.

from django.db import models
from django.contrib.auth.models import User


class CustomerProfile(models.Model):

    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Other", "Other"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    profile_image = models.ImageField(
        upload_to="customers/",
        blank=True,
        null=True
    )

    full_name = models.CharField(max_length=150)

    phone = models.CharField(max_length=20)

    date_of_birth = models.DateField(
        blank=True,
        null=True
    )

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True
    )

    ic_passport = models.CharField(
        max_length=30,
        blank=True
    )

    address = models.TextField(blank=True)

    emergency_contact = models.CharField(
        max_length=20,
        blank=True
    )

    company_name = models.CharField(
        max_length=150,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name
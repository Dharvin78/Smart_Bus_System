from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):

    OWNER = "Owner"
    ADMIN = "Admin"
    DRIVER = "Driver"
    CUSTOMER = "Customer"

    ROLE_CHOICES = [
        (OWNER, "Owner"),
        (ADMIN, "Admin"),
        (DRIVER, "Driver"),
        (CUSTOMER, "Customer"),
    ]

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

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=CUSTOMER
    )

    phone = models.CharField(
        max_length=20,
        blank=True
    )

    address = models.TextField(
        blank=True
    )

    city = models.CharField(
        max_length=100,
        blank=True
    )

    state = models.CharField(
        max_length=100,
        blank=True
    )

    postcode = models.CharField(
        max_length=20,
        blank=True
    )

    country = models.CharField(
        max_length=100,
        default="Malaysia"
    )

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True
    )

    profile_picture = models.ImageField(
        upload_to="profile_pictures/",
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.user.username} ({self.role})"
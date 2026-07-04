# Create your models here.
from django.db import models
from apps.vehicles.models import Vehicle


class Driver(models.Model):

    STATUS_CHOICES = [
        ("Available", "Available"),
        ("On Trip", "On Trip"),
        ("Leave", "Leave"),
        ("Inactive", "Inactive"),
    ]

    full_name = models.CharField(max_length=100)

    ic_passport = models.CharField(
        max_length=20,
        unique=True
    )

    phone = models.CharField(max_length=20)

    email = models.EmailField(
        blank=True,
        null=True
    )

    address = models.TextField(blank=True)

    driving_license = models.CharField(
        max_length=50,
        unique=True
    )

    license_expiry = models.DateField()

    assigned_vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="drivers"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Available"
    )

    photo = models.ImageField(
        upload_to="drivers/",
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return self.full_name
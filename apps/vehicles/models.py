# Create your models here.
from django.db import models


class Vehicle(models.Model):

    STATUS_CHOICES = [
        ("Available", "Available"),
        ("Booked", "Booked"),
        ("Maintenance", "Maintenance"),
        ("Inactive", "Inactive"),
    ]

    BUS_TYPE_CHOICES = [
        ("Mini Bus", "Mini Bus"),
        ("Standard Bus", "Standard Bus"),
        ("VIP Coach", "VIP Coach"),
    ]

    registration_number = models.CharField(
        max_length=20,
        unique=True
    )

    vehicle_name = models.CharField(
        max_length=100
    )

    bus_type = models.CharField(
        max_length=30,
        choices=BUS_TYPE_CHOICES
    )

    seat_capacity = models.PositiveIntegerField()

    manufacture_year = models.PositiveIntegerField()

    insurance_expiry = models.DateField()

    road_tax_expiry = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Available"
    )

    image = models.ImageField(
        upload_to="vehicles/",
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.registration_number} - {self.vehicle_name}"
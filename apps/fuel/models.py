# Create your models here.
from django.db import models
from django.utils import timezone

from apps.vehicles.models import Vehicle


class Fuel(models.Model):

    FUEL_TYPE_CHOICES = [
        ("Diesel", "Diesel"),
        ("Petrol", "Petrol"),
    ]

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name="fuel_records",
    )

    fuel_type = models.CharField(
        max_length=20,
        choices=FUEL_TYPE_CHOICES,
    )

    refill_date = models.DateField()

    litres = models.DecimalField(
        max_digits=8,
        decimal_places=2,
    )

    price_per_litre = models.DecimalField(
        max_digits=8,
        decimal_places=2,
    )

    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    fuel_station = models.CharField(
        max_length=150,
    )

    mileage = models.PositiveIntegerField(
        help_text="Vehicle mileage during refill (km)"
    )

    remarks = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        default=timezone.now,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-refill_date",
            "-created_at",
        ]

    def save(self, *args, **kwargs):
        self.total_cost = self.litres * self.price_per_litre
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.vehicle.registration_number} "
            f"- {self.refill_date}"
        )
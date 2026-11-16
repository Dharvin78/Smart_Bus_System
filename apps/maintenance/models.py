# Create your models here.
from django.db import models
from django.utils import timezone

from apps.vehicles.models import Vehicle


class Maintenance(models.Model):

    MAINTENANCE_TYPE_CHOICES = [
        ("Oil Change", "Oil Change"),
        ("Engine Service", "Engine Service"),
        ("Brake Service", "Brake Service"),
        ("Tyre Replacement", "Tyre Replacement"),
        ("Air Conditioning", "Air Conditioning"),
        ("Battery Replacement", "Battery Replacement"),
        ("General Inspection", "General Inspection"),
        ("Other", "Other"),
    ]

    STATUS_CHOICES = [
        ("Scheduled", "Scheduled"),
        ("In Progress", "In Progress"),
        ("Completed", "Completed"),
        ("Cancelled", "Cancelled"),
    ]

    MAINTENANCE_LABEL_CHOICES = [
        ("Yes", "Yes"),
        ("No", "No"),
    ]

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name="maintenance_records",
    )

    assigned_driver = models.ForeignKey(
        "drivers.Driver",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="maintenance_assignments",
        help_text="Driver assigned to this maintenance task"
    )

    maintenance_type = models.CharField(
        max_length=50,
        choices=MAINTENANCE_TYPE_CHOICES,
    )

    workshop = models.CharField(
        max_length=150,
    )

    service_date = models.DateField()

    start_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Scheduled maintenance start time"
    )

    end_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Scheduled maintenance end time"
    )

    next_service_date = models.DateField(
        blank=True,
        null=True,
    )

    mileage = models.PositiveIntegerField(
        help_text="Vehicle mileage (km)"
    )

    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Scheduled",
    )

    needs_maintenance = models.CharField(
        max_length=3,
        choices=MAINTENANCE_LABEL_CHOICES,
        default="No",
        help_text="Used for AI model training",
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

    start_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Scheduled maintenance start time"
    )

    end_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Scheduled maintenance end time"
    )

    class Meta:
        ordering = ["-service_date", "-created_at"]

    def __str__(self):
        return f"{self.vehicle.registration_number} - {self.maintenance_type}"
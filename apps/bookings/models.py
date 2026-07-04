from django.db import models
from django.utils import timezone

from apps.accounts.models import CustomerProfile
from apps.vehicles.models import Vehicle
from apps.drivers.models import Driver


class Booking(models.Model):

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Confirmed", "Confirmed"),
        ("Completed", "Completed"),
        ("Cancelled", "Cancelled"),
    ]

    PAYMENT_CHOICES = [
        ("Pending", "Pending"),
        ("Paid", "Paid"),
        ("Refunded", "Refunded"),
    ]

    booking_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
    )

    customer = models.ForeignKey(
        CustomerProfile,
        on_delete=models.CASCADE,
        related_name="bookings",
    )

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.PROTECT,
        related_name="bookings",
    )

    driver = models.ForeignKey(
        Driver,
        on_delete=models.PROTECT,
        related_name="bookings",
    )

    pickup_location = models.CharField(max_length=150)

    destination = models.CharField(max_length=150)

    travel_date = models.DateField()

    departure_time = models.TimeField()

    return_date = models.DateField(
        blank=True,
        null=True,
    )

    passenger_count = models.PositiveIntegerField()

    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    booking_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending",
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_CHOICES,
        default="Pending",
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
        ordering = ["-travel_date", "-created_at"]

    def __str__(self):
        return self.booking_number

    def save(self, *args, **kwargs):

        if not self.booking_number:

            today = timezone.now().strftime("%Y%m%d")

            latest = Booking.objects.filter(
                booking_number__startswith=f"SB{today}"
            ).order_by("-booking_number").first()

            if latest:

                last_number = int(latest.booking_number[-4:]) + 1

            else:

                last_number = 1

            self.booking_number = f"SB{today}{last_number:04d}"

        super().save(*args, **kwargs)
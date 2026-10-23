from django.db import models
from django.utils import timezone

from apps.customers.models import Customer
from apps.vehicles.models import Vehicle
from apps.drivers.models import Driver

from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from datetime import datetime

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
        Customer,
        on_delete=models.CASCADE,
        related_name="bookings",
    )

    vehicle = models.ForeignKey(
        Vehicle,
            on_delete=models.PROTECT,
            related_name="bookings",
            null=True,
            blank=True,
        )
        
    driver = models.ForeignKey(
            Driver,
            on_delete=models.PROTECT,
            related_name="bookings",
            null=True,
            blank=True,
        )
    
    pickup_location = models.CharField(max_length=150)

    destination = models.CharField(max_length=150)

    travel_date = models.DateField()

    departure_time = models.TimeField()

    return_date = models.DateField(
        blank=True,
        null=True,
    )

    passenger_count = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(42),
        ],
        help_text="Maximum 42 passengers. Two seats are reserved for the tour guide and additional driver.",
    )

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

# 6 Hours Waiting Time for Approval (databse field to store the approval time)
    approval_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date and time the booking was approved."
    )

    payment_deadline = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Deadline for completing payment."
    )

    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date and time the booking was cancelled.",
    )

    rejection_reason = models.TextField(
        blank=True,
        default="",
        help_text="Reason provided when the booking is rejected."
    )

    travel_reminder_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date and time the travel details email was sent."
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

    @property
    def departure_datetime(self):
        departure = datetime.combine(
            self.travel_date,
            self.departure_time,
        )
        return timezone.make_aware(
            departure,
            timezone.get_current_timezone(),
        )

    def clean(self):
        super().clean()

        if self.passenger_count is not None and self.passenger_count > 42:
            raise ValidationError({
                "passenger_count": "Maximum 42 passengers allowed."
            })

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
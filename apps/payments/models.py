from django.db import models
from apps.bookings.models import Booking

from django.db.models import Q


class Payment(models.Model):

    PAYMENT_METHOD_CHOICES = [
        ("Credit Card", "Credit Card"),
        ("Debit Card", "Debit Card"),
        ("Online Banking", "Online Banking"),
        ("E-Wallet", "E-Wallet"),
        ("Bank Transfer", "Bank Transfer"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Paid", "Paid"),
        ("Failed", "Failed"),
        ("Partially Paid", "Partially Paid"),
        ("Refunded", "Refunded"),
        ("Cancelled", "Cancelled"),
        ("Partially Refunded", "Partially Refunded"),
    ]

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="payments",
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    payment_method = models.CharField(
        max_length=30,
        choices=PAYMENT_METHOD_CHOICES,
        blank=True,
        null=True,
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="Pending",
    )
    
# Refund information
    refund_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    refund_date = models.DateTimeField(
        null=True,
        blank=True,
    )

    refund_transaction_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )

    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    payment_date = models.DateField()

    remarks = models.TextField(
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["booking"],
                condition=models.Q(payment_status="Paid"),
                name="unique_paid_payment_per_booking",
            ),
        ]

    def __str__(self):
        return f"Payment #{self.id} - {self.booking}"
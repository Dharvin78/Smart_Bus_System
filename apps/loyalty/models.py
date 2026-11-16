from datetime import timedelta
from decimal import Decimal

from django.db import models
from django.db.models import Q
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
)
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from apps.customers.models import Customer


# TABLE 1: Loyalty Account
class LoyaltyAccount(models.Model):

    TIER_CHOICES = [
        ("Bronze", "Bronze"),
        ("Silver", "Silver"),
        ("Gold", "Gold"),
        ("Platinum", "Platinum"),
    ]

    customer = models.OneToOneField(
        Customer,
        on_delete=models.CASCADE,
        related_name="loyalty_account"
    )

    points_balance = models.PositiveIntegerField(default=0)

    lifetime_points = models.PositiveIntegerField(default=0)

    membership_tier = models.CharField(
        max_length=20,
        choices=TIER_CHOICES,
        default="Bronze"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def update_tier(self):
        points = self.lifetime_points

        if points >= 3000:
            self.membership_tier = "Platinum"
        elif points >= 1500:
            self.membership_tier = "Gold"
        elif points >= 500:
            self.membership_tier = "Silver"
        else:
            self.membership_tier = "Bronze"

    def __str__(self):
        return f"{self.customer} - {self.membership_tier}"


# TABLE 2: Loyalty Reward
class LoyaltyReward(models.Model):

    name = models.CharField(max_length=100)

    description = models.TextField(blank=True)

    points_required = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    discount_percentage = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(100)
        ]
    )

    max_discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))]
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"{self.name} - "
            f"{self.discount_percentage}% Discount"
        )


# TABLE 3: Loyalty Transaction
class LoyaltyTransaction(models.Model):

    TRANSACTION_TYPES = [
        ("Earned", "Earned"),
        ("Redeemed", "Redeemed"),
        ("Expired", "Expired"),
        ("Adjustment", "Adjustment"),
        ("Reversal", "Reversal"),
    ]

    account = models.ForeignKey(
        LoyaltyAccount,
        on_delete=models.CASCADE,
        related_name="transactions"
    )

    booking = models.ForeignKey(
        "bookings.Booking",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    reward = models.ForeignKey(
        LoyaltyReward,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES
    )

    # Positive for earned, negative for deductions
    points = models.IntegerField()

    # Remaining points from an earning transaction
    remaining_points = models.PositiveIntegerField(default=0)

    earned_at = models.DateTimeField(
        null=True,
        blank=True
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True
    )

    description = models.CharField(
        max_length=255,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["booking"],
                condition=Q(
                    transaction_type="Earned",
                    booking__isnull=False
                ),
                name="unique_loyalty_earning_per_booking"
            )
        ]

    def save(self, *args, **kwargs):

        # Assign expiry only when first creating
        # an earned-points transaction.
        if self._state.adding and self.transaction_type == "Earned":

            if self.earned_at is None:
                self.earned_at = timezone.now()

            if self.expires_at is None:
                self.expires_at = (
                    self.earned_at + relativedelta(months=6)
                )

            self.remaining_points = self.points

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.account.customer} - "
            f"{self.transaction_type}: {self.points}"
        )

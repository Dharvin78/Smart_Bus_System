
from django.db import transaction
from django.utils import timezone

from apps.bookings.models import Booking
from apps.payments.models import Payment
from apps.loyalty.models import (
    LoyaltyAccount,
    LoyaltyReward,
    LoyaltyTransaction,
)
from django.db.models import Sum
from decimal import Decimal, ROUND_HALF_UP

POINTS_PER_RM = 10

@transaction.atomic
def award_loyalty_points(booking):
    """
    Award 1 point for every RM10 spent.

    Points are awarded only when:
    - Booking status is Completed
    - Payment status is Paid
    - Points have not already been awarded
    """

    if booking.booking_status != "Completed":
        return False

    if booking.payment_status != "Paid":
        return False

    points = int(booking.total_price // POINTS_PER_RM)

    if points <= 0:
        return False

    account, created = LoyaltyAccount.objects.get_or_create(
        customer=booking.customer
    )

    # Lock the account to prevent concurrent balance updates.
    account = LoyaltyAccount.objects.select_for_update().get(
        pk=account.pk
    )

    # Prevent duplicate point awards.
    if LoyaltyTransaction.objects.filter(
        booking=booking,
        transaction_type="Earned"
    ).exists():
        return False

    LoyaltyTransaction.objects.create(
        account=account,
        booking=booking,
        transaction_type="Earned",
        points=points,
        description=f"Points earned from {booking.booking_number}"
    )

    account.points_balance += points
    account.lifetime_points += points

    account.update_tier()

    account.save()

    return True

@transaction.atomic
def expire_loyalty_points(account):
    """
    Expire unused loyalty points after 6 months.

    - Only earned points can expire.
    - Redeemed points cannot expire again.
    - Membership tier remains unchanged.
    """

    account = LoyaltyAccount.objects.select_for_update().get(
        pk=account.pk
    )

    now = timezone.now()

    expired_transactions = (
        LoyaltyTransaction.objects.select_for_update()
        .filter(
            account=account,
            transaction_type="Earned",
            expires_at__lte=now,
            remaining_points__gt=0
        )
        .order_by("expires_at", "id")
    )

    total_expired = 0

    for earning in expired_transactions:
        expired_points = earning.remaining_points

        LoyaltyTransaction.objects.create(
            account=account,
            booking=earning.booking,
            transaction_type="Expired",
            points=-expired_points,
            description=(
                f"Points expired from earning #{earning.id}"
            )
        )

        earning.remaining_points = 0
        earning.save(update_fields=["remaining_points"])

        total_expired += expired_points

    if total_expired > 0:
        account.points_balance -= total_expired
        account.save(update_fields=["points_balance", "updated_at"])

    return total_expired

@transaction.atomic
def redeem_loyalty_reward(booking, reward_id):
    """
    Redeem one percentage-based reward per booking.

    Booking, loyalty points, and pending payments
    are updated within one database transaction.
    """

    # Lock and refresh the booking first.
    booking = Booking.objects.select_for_update().get(
        pk=booking.pk
    )

    if booking.booking_status != "Confirmed":
        raise ValueError(
            "Only confirmed bookings can use loyalty rewards."
        )

    if booking.payment_status != "Pending":
        raise ValueError(
            "Loyalty rewards must be redeemed before payment."
        )

    if Payment.objects.filter(
        booking=booking,
        payment_status="Paid"
    ).exists():
        raise ValueError("This booking has already been paid.")

    if (
        booking.loyalty_reward_id is not None
        or LoyaltyTransaction.objects.filter(
            booking=booking,
            transaction_type="Redeemed"
        ).exists()
    ):
        raise ValueError(
            "A loyalty reward has already been redeemed."
        )

    reward = LoyaltyReward.objects.get(
        pk=reward_id,
        is_active=True
    )

    account = LoyaltyAccount.objects.select_for_update().get(
        customer=booking.customer
    )

    # Remove expired points before redemption.
    expire_loyalty_points(account)
    account.refresh_from_db()

    original_price = booking.total_price

    if original_price is None or original_price <= 0:
        raise ValueError("Invalid booking price.")

    # Calculate percentage discount with a maximum cap.
    discount = (
        original_price
        * Decimal(reward.discount_percentage)
        / Decimal("100")
    )

    discount = min(discount, reward.max_discount)

    discount = discount.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    if discount <= 0:
        raise ValueError("Invalid loyalty discount.")

    if account.points_balance < reward.points_required:
        raise ValueError("Insufficient loyalty points.")

    points_needed = reward.points_required

    earnings = (
        LoyaltyTransaction.objects.select_for_update()
        .filter(
            account=account,
            transaction_type="Earned",
            remaining_points__gt=0,
            expires_at__gt=timezone.now()
        )
        .order_by("expires_at", "pk")
    )

    for earning in earnings:
        if points_needed <= 0:
            break

        used = min(earning.remaining_points, points_needed)

        earning.remaining_points -= used
        earning.save(update_fields=["remaining_points"])

        points_needed -= used

    if points_needed > 0:
        raise ValueError(
            "Insufficient unexpired loyalty points."
        )

    final_price = original_price - discount

    if final_price <= 0:
        raise ValueError(
            "The final booking price must be greater than zero."
        )

    # Save the redemption history.
    LoyaltyTransaction.objects.create(
        account=account,
        booking=booking,
        reward=reward,
        transaction_type="Redeemed",
        points=-reward.points_required,
        description=(
            f"{reward.discount_percentage}% discount "
            f"for booking {booking.booking_number}"
        )
    )

    # Update customer loyalty balance.
    account.points_balance -= reward.points_required
    account.save(
        update_fields=["points_balance", "updated_at"]
    )

    # Save discount details on the booking.
    booking.original_price = original_price
    booking.loyalty_discount = discount
    booking.loyalty_reward = reward
    booking.total_price = final_price

    booking.save(
        update_fields=[
            "original_price",
            "loyalty_discount",
            "loyalty_reward",
            "total_price",
            "updated_at",
        ]
    )

    # Synchronize existing pending payment records.
    Payment.objects.filter(
        booking=booking,
        payment_status="Pending"
    ).update(amount=final_price)

    return {
        "original_price": original_price,
        "discount": discount,
        "final_price": final_price,
        "points_used": reward.points_required,
    }

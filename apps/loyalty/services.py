
from decimal import Decimal, ROUND_HALF_UP

from dateutil.relativedelta import relativedelta
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.bookings.models import Booking
from apps.payments.models import Payment
from apps.loyalty.models import (
    LoyaltyAccount,
    LoyaltyReward,
    LoyaltyTransaction,
)

RM_PER_POINT = 10
SPENDABLE_TRANSACTION_TYPES = ("Earned", "Reversal")

@transaction.atomic
def award_loyalty_points(booking, *, earned_at=None):
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

    if booking.total_price is None:
        return False

    points = int(booking.total_price // RM_PER_POINT)

    if points <= 0:
        return False

    account, _ = LoyaltyAccount.objects.get_or_create(
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
        earned_at=earned_at,
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

    - Earned and restored points can expire.
    - Redeemed points cannot expire again.
    - Membership tier remains unchanged.
    """

    LoyaltyAccount.objects.filter(pk=account.pk).update(updated_at=F("updated_at"))
    account = LoyaltyAccount.objects.get(pk=account.pk)

    now = timezone.now()

    expired_transactions = (
        LoyaltyTransaction.objects.select_for_update()
        .filter(
            account=account,
            transaction_type__in=SPENDABLE_TRANSACTION_TYPES,
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
                f"Points expired from transaction #{earning.id}"
            )
        )

        earning.remaining_points = 0
        earning.save(update_fields=["remaining_points"])

        total_expired += expired_points

    if total_expired > 0:
        account.points_balance -= total_expired
        account.save(update_fields=["points_balance", "updated_at"])

    return total_expired


def current_loyalty_account(customer):
    account = LoyaltyAccount.objects.filter(customer=customer).first()
    if account and account.transactions.filter(
        transaction_type__in=SPENDABLE_TRANSACTION_TYPES,
        expires_at__lte=timezone.now(),
        remaining_points__gt=0,
    ).exists():
        expire_loyalty_points(account)
        account.refresh_from_db()
    return account


@transaction.atomic
def redeem_loyalty_reward(booking, reward_id):
    """
    Redeem one percentage-based reward per booking.

    Booking, loyalty points, and pending payments
    are updated within one database transaction.
    """

    # Serialize redemption with payment, including on SQLite.
    Booking.objects.filter(pk=booking.pk).update(updated_at=F("updated_at"))
    booking = Booking.objects.get(pk=booking.pk)

    if booking.booking_status != "Confirmed":
        raise ValueError(
            "Only confirmed bookings can use loyalty rewards."
        )

    if booking.payment_status != "Pending":
        raise ValueError(
            "Loyalty rewards must be redeemed before payment."
        )

    if timezone.now() >= (booking.payment_deadline or booking.departure_datetime):
        raise ValueError("The payment deadline for this booking has passed.")

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

    reward = LoyaltyReward.objects.filter(
        pk=reward_id,
        is_active=True
    ).first()
    if reward is None:
        raise ValueError("This loyalty reward is no longer available.")

    account = LoyaltyAccount.objects.select_for_update().filter(
        customer=booking.customer
    ).first()
    if account is None:
        raise ValueError("Insufficient loyalty points.")

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
            transaction_type__in=SPENDABLE_TRANSACTION_TYPES,
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


@transaction.atomic
def restore_redeemed_points(booking, redemption, now):
    account = LoyaltyAccount.objects.select_for_update().get(
        pk=redemption.account_id, customer=booking.customer,
    )
    if account.transactions.filter(booking=booking, transaction_type="Reversal").exists():
        return 0

    points = -redemption.points
    account.transactions.create(
        booking=booking,
        reward=redemption.reward,
        transaction_type="Reversal",
        points=points,
        remaining_points=points,
        expires_at=now + relativedelta(months=6),
        description=f"Points returned after cancelling {booking.booking_number}",
    )
    account.points_balance += points
    account.save(update_fields=["points_balance", "updated_at"])
    return points

from django.contrib import messages
from django.db import OperationalError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from apps.accounts.decorators import customer_required
from apps.bookings.models import Booking
from apps.helpdesk.services.data_access import get_customer_for_user

from .models import LoyaltyReward
from .services import current_loyalty_account, redeem_loyalty_reward


@customer_required
@require_GET
def dashboard(request):
    customer = get_customer_for_user(request.user)
    if customer is None:
        messages.error(request, "Customer profile not found.")
        return redirect("dashboard")

    account = current_loyalty_account(customer)
    rewards = LoyaltyReward.objects.filter(is_active=True).order_by("points_required", "pk")
    history = (
        account.transactions.select_related("booking").order_by("-created_at", "-pk")[:25]
        if account else []
    )
    return render(request, "loyalty/dashboard.html", {
        "account": account,
        "rewards": rewards,
        "history": history,
    })


@customer_required
@require_POST
def redeem(request, booking_id):
    customer = get_customer_for_user(request.user)
    if customer is None:
        messages.error(request, "Customer profile not found.")
        return redirect("dashboard")

    booking = get_object_or_404(Booking, pk=booking_id, customer=customer)
    try:
        reward_id = int(request.POST.get("reward_id", ""))
    except ValueError:
        messages.error(request, "Select a loyalty reward.")
    else:
        try:
            result = redeem_loyalty_reward(booking, reward_id)
        except ValueError as exc:
            messages.error(request, str(exc))
        except OperationalError:
            messages.error(request, "Rewards are temporarily unavailable. Please try again.")
        else:
            messages.success(
                request,
                f"Reward applied. You saved RM {result['discount']:.2f}.",
            )

    return redirect(f"{reverse('payments:payment_create')}?booking={booking.pk}")

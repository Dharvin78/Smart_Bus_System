import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from django.utils import timezone

from .models import Booking
from apps.helpdesk.services.data_access import get_customer_for_user
from apps.loyalty.models import LoyaltyTransaction
from decimal import Decimal, InvalidOperation
from django.db import OperationalError, transaction
from django.views.decorators.http import require_http_methods
from apps.bookings.availability_services import (
    has_booking_date_conflict,
    has_maintenance_date_conflict,
    expire_pending_bookings,
)
from django.core.exceptions import PermissionDenied
from datetime import timedelta
from .forms import (
    BookingForm,
    BookingReviewForm,
    BookingRejectForm,
    CustomerBookingForm,
)

from apps.notifications.services import notify_booking_staff
from .customer_updates import send_customer_booking_update
from .cancellation_services import (
    cancel_customer_booking,
    cancellation_quote,
    cancellation_quote_key,
)
from apps.accounts.decorators import (
    admin_required,
    customer_required,
    driver_required,
)

logger = logging.getLogger(__name__)

@admin_required
def booking_list(request):
    """
    Display all bookings with search and pagination.
    Automatically cancel expired pending bookings.
    """

    # Cancel pending bookings whose departure time has passed.
    expire_pending_bookings()

    search = request.GET.get("search", "")
    
    bookings = Booking.objects.select_related(
        "customer",
        "vehicle",
        "driver",
    ).order_by("-travel_date")

    if search:
        bookings = bookings.filter(
            Q(booking_number__icontains=search) |
            Q(customer__first_name__icontains=search) |
            Q(customer__last_name__icontains=search) |
            Q(vehicle__registration_number__icontains=search) |
            Q(driver__full_name__icontains=search) |
            Q(destination__icontains=search)
        )

    paginator = Paginator(bookings, 10)

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "bookings": page_obj,
        "search": search,
        "is_paginated": page_obj.has_other_pages(),
    }

    return render(
        request,
        "bookings/booking_list.html",
        context,
    )

def staff_only(request):
    return request.user.profile.role in ["Owner", "Admin"]

@customer_required
def booking_create(request):
    # Only Customers can submit booking requests.
    if request.user.profile.role != "Customer":
        messages.error(
            request,
            "Only customers can submit booking requests."
        )
        return redirect("bookings:booking_list")

    customer = get_customer_for_user(request.user)

    if not customer:
        messages.error(
            request,
            "No customer profile is associated with your account. "
            "Please contact the administrator."
        )
        return redirect("dashboard")

    if request.method == "POST":
        form = CustomerBookingForm(request.POST)

        if form.is_valid():
            booking = form.save(commit=False)

            # Assign trusted values on the server.
            booking.customer = customer
            booking.booking_status = "Pending"
            booking.payment_status = "Pending"
            booking.vehicle = None
            booking.driver = None
            booking.total_price = 0
            booking.save()

            bookings_url = request.build_absolute_uri(reverse("bookings:customer_bookings"))
            transaction.on_commit(
                lambda: send_customer_booking_update(booking, "submitted", bookings_url)
            )

            # Notify Owners and Admins inside the system.
            try:
                notify_booking_staff(
                    title="New Booking Requires Review",
                    message=(
                        f"Booking {booking.booking_number} has been "
                        f"submitted by {customer.first_name} "
                        f"{customer.last_name} and requires review."
                    ),
                    notification_type="info",
                    link="/bookings/",
                )
            except Exception:
                logger.exception(
                    "Failed to notify staff about booking %s",
                    booking.booking_number,
                )

            messages.success(
                request,
                "Your booking request has been submitted. "
                "Please wait for the Admin/Owner to review it."
            )

            return redirect("bookings:customer_bookings")

    else:
        form = CustomerBookingForm()

    return render(
        request,
        "bookings/booking_form.html",
        {
            "form": form,
            "title": "Request a Booking",
        },
    )

@driver_required
def driver_trips(request):

    # Make sure the logged-in user is a Driver
    if request.user.profile.role != "Driver":
        messages.error(
            request,
            "You do not have permission to access assigned trips."
        )

        return redirect("dashboard")

    # Get trips assigned to this driver
    bookings = Booking.objects.filter(
        driver__user=request.user
    ).select_related(
        "vehicle",
        "driver"
    ).order_by(
        "travel_date",
        "departure_time"
    )

    context = {
        "bookings": bookings,
    }

    return render(
        request,
        "bookings/driver_trips.html",
        context
    )

@customer_required
def customer_bookings(request):
    if request.user.profile.role != "Customer":
        messages.error(
            request,
            "You do not have permission to access customer bookings."
        )
        return redirect("dashboard")

    customer = get_customer_for_user(request.user)

    if not customer:
        messages.error(
            request,
            "No customer profile is associated with your account."
        )
        return redirect("dashboard")

    bookings = Booking.objects.filter(
        customer=customer
    ).select_related(
        "vehicle",
        "driver",
    ).prefetch_related(
        "driver_review", "payments",
        Prefetch(
            "loyaltytransaction_set",
            queryset=LoyaltyTransaction.objects.filter(transaction_type__in=["Redeemed", "Reversal"]),
            to_attr="cancellation_points",
        ),
    ).order_by(
        "-travel_date",
        "-departure_time",
    )

    now = timezone.now()
    for booking in bookings:
        booking.cancel_allowed = (
            booking.booking_status == "Confirmed"
            and booking.departure_datetime - now >= timedelta(hours=4)
        )
        booking.points_used = -sum(
            entry.points for entry in booking.cancellation_points if entry.transaction_type == "Redeemed"
        )
        booking.points_returned = sum(
            entry.points for entry in booking.cancellation_points if entry.transaction_type == "Reversal"
        )
        booking.show_cancellation_details = (
            booking.booking_status == "Cancelled" and (booking.refund_amount or booking.points_used)
        )

    return render(
        request,
        "bookings/customer_bookings.html",
        {
            "bookings": bookings,
        }
    )

@customer_required
@require_http_methods(["GET", "POST"])
def customer_cancel_booking(request, pk):
    customer = get_customer_for_user(request.user)

    if not customer:
        raise PermissionDenied(
            "No customer profile is associated with your account."
        )

    if request.method == "GET":
        booking = get_object_or_404(Booking, pk=pk, customer=customer)
        try:
            quote = cancellation_quote(booking)
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect("bookings:customer_bookings")
        return render(request, "bookings/cancellation_confirm.html", {
            "booking": booking,
            "quote": quote,
            "quote_key": cancellation_quote_key(quote),
        })

    try:
        booking, quote = cancel_customer_booking(
            pk, customer, request.user, request.META.get("REMOTE_ADDR"),
            expected_quote=request.POST.get("quote"),
        )
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("bookings:customer_bookings")
    except OperationalError:
        messages.error(request, "Cancellation is temporarily unavailable. Please try again.")
        return redirect("bookings:customer_bookings")

    bookings_url = request.build_absolute_uri(reverse("bookings:customer_bookings"))
    transaction.on_commit(
        lambda: send_customer_booking_update(
            booking, "cancelled", bookings_url, cancellation=quote,
        )
    )

    messages.success(
        request,
        f"Booking {booking.booking_number} has been cancelled."
    )

    return redirect("bookings:customer_bookings")

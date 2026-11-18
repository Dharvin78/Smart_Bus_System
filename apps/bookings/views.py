import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone

from apps.audit.models import AuditLog
from .models import Booking
from apps.helpdesk.services.data_access import get_customer_for_user
from apps.payments.models import Payment
from django.utils import timezone
from decimal import Decimal, InvalidOperation
from django.db import transaction
from django.views.decorators.http import require_POST
from apps.bookings.availability_services import (
    has_booking_date_conflict,
    has_maintenance_date_conflict,
    expire_pending_bookings,
)
from django.core.exceptions import PermissionDenied
from django.db.models import F
from datetime import timedelta
from .forms import (
    BookingForm,
    BookingReviewForm,
    BookingRejectForm,
    CustomerBookingForm,
)

from apps.emails.services import send_booking_submitted_email
from apps.notifications.services import (
    notify_customer,
    notify_booking_staff,
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

            # Notify the customer inside the system.
            try:
                notify_customer(
                    booking=booking,
                    title="Booking Submitted",
                    message=(
                        f"Your booking {booking.booking_number} "
                        "has been submitted and is awaiting approval."
                    ),
                    notification_type="success",
                )
            except Exception:
                logger.exception(
                    "Failed to create customer notification "
                    "for booking %s",
                    booking.booking_number,
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

            # Email the customer without preventing the booking
            # from being saved if the email service fails.
            try:
                email_sent = send_booking_submitted_email(booking)

                if not email_sent:
                    logger.warning(
                        "No customer email available for booking %s",
                        booking.booking_number,
                    )
            except Exception:
                logger.exception(
                    "Failed to send submission email for booking %s",
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
        "driver_review"
    ).order_by(
        "-travel_date",
        "-departure_time",
    )

    return render(
        request,
        "bookings/customer_bookings.html",
        {
            "bookings": bookings,
        }
    )

@customer_required
@require_POST
def customer_cancel_booking(request, pk):
    customer = get_customer_for_user(request.user)

    if not customer:
        raise PermissionDenied(
            "No customer profile is associated with your account."
        )

    with transaction.atomic():
        booking = get_object_or_404(
            Booking.objects.select_for_update(),
            pk=pk,
            customer=customer,
        )

        if booking.booking_status != "Pending":
            messages.error(
                request,
                "Only pending booking requests can be cancelled."
            )
            return redirect("bookings:customer_bookings")

        booking.booking_status = "Cancelled"
        booking.save(update_fields=["booking_status", "updated_at"])

        AuditLog.objects.create(
            user=request.user,
            module="Booking",
            action="CANCEL",
            booking=booking,
            customer=customer,
            description=(
                f"Customer {request.user.username} cancelled "
                f"booking {booking.booking_number} before approval."
            ),
            ip_address=request.META.get("REMOTE_ADDR"),
        )

    messages.success(
        request,
        f"Booking {booking.booking_number} has been cancelled."
    )

    return redirect("bookings:customer_bookings")
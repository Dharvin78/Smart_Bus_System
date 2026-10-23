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
from django.core.exceptions import PermissionDenied
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
    """

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


@admin_required
def booking_review(request, pk):
    from datetime import datetime, timedelta

    from apps.vehicles.models import Vehicle
    from apps.drivers.models import Driver

    booking = get_object_or_404(
        Booking.objects.select_related("customer", "vehicle", "driver"),
        pk=pk,
    )

    if booking.booking_status != "Pending":
        messages.error(request, "Only pending bookings can be reviewed.")
        return redirect("bookings:booking_list")

    available_vehicles = Vehicle.objects.filter(
        status="Available"
    ).order_by("vehicle_name")

    available_drivers = Driver.objects.filter(
        status="Available"
    ).order_by("full_name")

    action = request.POST.get("action") if request.method == "POST" else None

    approval_form = BookingReviewForm(
        request.POST if action == "approve" else None,
        vehicle_queryset=available_vehicles,
        driver_queryset=available_drivers,
    )

    reject_form = BookingRejectForm(
        request.POST if action == "reject" else None
    )

    if request.method == "POST":
        if action not in ("approve", "reject"):
            messages.error(request, "Invalid booking action.")
            return redirect("bookings:booking_review", pk=pk)

        # Validate the appropriate form only.
        if action == "approve" and not approval_form.is_valid():
            messages.error(request, "Please correct the approval fields.")

        elif action == "reject" and not reject_form.is_valid():
            messages.error(request, "Please correct the rejection notes.")

        else:
            try:
                with transaction.atomic():
                    # Recheck booking state inside the transaction.
                    locked_booking = Booking.objects.select_for_update().get(
                        pk=pk
                    )

                    if locked_booking.booking_status != "Pending":
                        raise ValueError(
                            "This booking has already been reviewed."
                        )

                    departure = timezone.make_aware(
                        datetime.combine(
                            locked_booking.travel_date,
                            locked_booking.departure_time,
                        ),
                        timezone.get_current_timezone(),
                    )

                    if timezone.now() >= departure:
                        raise ValueError(
                            "The scheduled departure time has passed. "
                            "This booking can no longer be reviewed."
                        )

                    if action == "reject":
                        reason = reject_form.cleaned_data["reason"]

                        locked_booking.booking_status = "Cancelled"
                        locked_booking.rejection_reason = reason
                        locked_booking.cancelled_at = timezone.now()
                        locked_booking.save(update_fields=[
                            "booking_status",
                            "rejection_reason",
                            "cancelled_at",
                            "updated_at",
                        ])

                        AuditLog.objects.create(
                            user=request.user,
                            module="Booking",
                            action="REJECT",
                            booking=locked_booking,
                            customer=locked_booking.customer,
                            description=(
                                f"Booking {locked_booking.booking_number} "
                                f"rejected by {request.user.username}. "
                                f"Reason: {reason or 'No reason provided'}."
                            ),
                            ip_address=request.META.get("REMOTE_ADDR"),
                        )

                    else:
                        vehicle_id = approval_form.cleaned_data["vehicle"].pk
                        driver_id = approval_form.cleaned_data["driver"].pk
                        total_price = approval_form.cleaned_data["total_price"]
                        notes = approval_form.cleaned_data["approval_notes"]

                        vehicle = Vehicle.objects.select_for_update().get(
                            pk=vehicle_id
                        )
                        driver = Driver.objects.select_for_update().get(
                            pk=driver_id
                        )

                        if vehicle.status != "Available":
                            raise ValueError(
                                "The selected vehicle is no longer available."
                            )

                        if driver.status != "Available":
                            raise ValueError(
                                "The selected driver is no longer available."
                            )

                        # Enforce actual bus capacity too.
                        if locked_booking.passenger_count > min(
                            42, max(0, vehicle.seat_capacity - 2)
                        ):
                            raise ValueError(
                                "This vehicle cannot accommodate the "
                                "passengers plus two reserved seats."
                            )

                        approved_at = timezone.now()

                        # Payment must also finish before departure.
                        deadline = min(
                            approved_at + timedelta(hours=6),
                            departure,
                        )

                        locked_booking.vehicle = vehicle
                        locked_booking.driver = driver
                        locked_booking.total_price = total_price
                        locked_booking.booking_status = "Confirmed"
                        locked_booking.payment_status = "Pending"
                        locked_booking.approval_time = approved_at
                        locked_booking.payment_deadline = deadline
                        locked_booking.remarks = (
                            f"{locked_booking.remarks}\n"
                            f"Approval notes: {notes}"
                        ).strip() if notes else locked_booking.remarks

                        locked_booking.save()

                        vehicle.status = "Booked"
                        vehicle.save(update_fields=["status"])

                        driver.status = "Reserved"
                        driver.save(update_fields=["status"])

                        # Reuse an existing Pending record, if any.
                        payment = (
                            Payment.objects.filter(
                                booking=locked_booking,
                                payment_status="Pending",
                            )
                            .order_by("-created_at", "-pk")
                            .first()
                        )

                        if payment is None:
                            payment = Payment(
                                booking=locked_booking,
                                payment_status="Pending",
                            )

                        payment.amount = total_price
                        payment.payment_method = "Online Banking"
                        payment.payment_date = timezone.localdate()
                        payment.save()

                        AuditLog.objects.create(
                            user=request.user,
                            module="Booking",
                            action="APPROVE",
                            booking=locked_booking,
                            customer=locked_booking.customer,
                            description=(
                                f"Booking {locked_booking.booking_number} "
                                f"approved by {request.user.username}. "
                                f"Price: RM {total_price:.2f}. "
                                f"Vehicle: {vehicle.registration_number}. "
                                f"Driver: {driver.full_name}. "
                                f"Payment deadline: "
                                f"{timezone.localtime(deadline):%d/%m/%Y %I:%M %p}. "
                                f"Notes: {notes or 'None'}."
                            ),
                            ip_address=request.META.get("REMOTE_ADDR"),
                        )

            except ValueError as exc:
                messages.error(request, str(exc))
            else:
                if action == "approve":
                    messages.success(
                        request,
                        "Booking approved. The customer must pay "
                        "before the payment deadline."
                    )
                else:
                    messages.success(request, "Booking rejected.")

                return redirect("bookings:booking_list")

    return render(
        request,
        "bookings/booking_review.html",
        {
            "booking": booking,
            "form": approval_form,
            "approval_form": approval_form,
            "reject_form": reject_form,
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
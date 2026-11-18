
from datetime import datetime, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.accounts.decorators import admin_required
from apps.audit.models import AuditLog
from apps.vehicles.models import Vehicle
from apps.drivers.models import Driver
from apps.payments.models import Payment

from .models import Booking
from .customer_updates import send_customer_booking_update
from .forms import BookingReviewForm, BookingRejectForm
from .availability_services import (
    has_booking_date_conflict,
    has_maintenance_date_conflict,
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

    # Include vehicles that are not manually inactive.
    # Booking and maintenance conflicts will be checked separately.
    available_vehicles = Vehicle.objects.exclude(
        status="Inactive"
    ).order_by("vehicle_name")

    # Exclude drivers who are manually unavailable.
    available_drivers = Driver.objects.exclude(
        status__in=["Leave", "Inactive"]
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

                    # Acquire a SQLite write lock before checking availability.
                    # This serializes competing booking approvals.
                    Booking.objects.filter(pk=pk).update(
                        updated_at=F("updated_at")
                    )

                    # Reload the booking after acquiring the write lock.
                    locked_booking = Booking.objects.get(pk=pk)

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
                        
                        # Check manually restricted vehicles.
                        if vehicle.status == "Inactive":
                            raise ValueError(
                                "The selected vehicle is inactive."
                            )

                        # Check manually restricted drivers.
                        if driver.status in ("Leave", "Inactive"):
                            raise ValueError(
                                "The selected driver is unavailable."
                            )

                        # Check overlapping vehicle bookings.
                        if has_booking_date_conflict(
                            travel_date=locked_booking.travel_date,
                            return_date=locked_booking.return_date,
                            vehicle=vehicle,
                            exclude_booking_id=locked_booking.pk,
                        ):
                            raise ValueError(
                                "The selected vehicle already has a confirmed "
                                "booking during the requested travel dates."
                            )

                        # Check overlapping driver bookings.
                        if has_booking_date_conflict(
                            travel_date=locked_booking.travel_date,
                            return_date=locked_booking.return_date,
                            driver=driver,
                            exclude_booking_id=locked_booking.pk,
                        ):
                            raise ValueError(
                                "The selected driver already has a confirmed "
                                "booking during the requested travel dates."
                            )

                        
                        # Check vehicle maintenance conflicts.
                        if has_maintenance_date_conflict(
                            travel_date=locked_booking.travel_date,
                            return_date=locked_booking.return_date,
                            vehicle=vehicle,
                        ):
                            raise ValueError(
                                "The selected vehicle has scheduled or ongoing "
                                "maintenance during the requested travel dates."
                            )

                        # Check driver maintenance assignments.
                        if has_maintenance_date_conflict(
                            travel_date=locked_booking.travel_date,
                            return_date=locked_booking.return_date,
                            driver=driver,
                        ):
                            raise ValueError(
                                "The selected driver has a maintenance assignment "
                                "during the requested travel dates."
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

                        # Final availability validation before assigning resources.
                        if has_booking_date_conflict(
                            travel_date=locked_booking.travel_date,
                            return_date=locked_booking.return_date,
                            vehicle=vehicle,
                            exclude_booking_id=locked_booking.pk,
                        ):
                            raise ValueError(
                                f"Vehicle {vehicle.registration_number} is already assigned "
                                "to another confirmed booking during these dates."
                            )

                        if has_booking_date_conflict(
                            travel_date=locked_booking.travel_date,
                            return_date=locked_booking.return_date,
                            driver=driver,
                            exclude_booking_id=locked_booking.pk,
                        ):
                            raise ValueError(
                                f"Driver {driver.full_name} is already assigned "
                                "to another confirmed booking during these dates."
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

                    event = "approved" if action == "approve" else "rejected"
                    bookings_url = request.build_absolute_uri(reverse("bookings:customer_bookings"))
                    transaction.on_commit(
                        lambda: send_customer_booking_update(locked_booking, event, bookings_url)
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

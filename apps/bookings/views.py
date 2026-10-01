from urllib import request

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone

from apps.audit.models import AuditLog
from .models import Booking
from .forms import BookingForm, BookingReviewForm
from apps.emails.services import send_booking_confirmation
from apps.helpdesk.services.data_access import get_customer_for_user


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

@login_required
def booking_create(request):
    if not staff_only(request):
        messages.error(
            request,
            "You do not have permission to create bookings."
        )
        return redirect("bookings:customer_bookings")

    if request.method == "POST":

        form = BookingForm(request.POST)

        if form.is_valid():

            vehicle = form.cleaned_data["vehicle"]

            passengers = form.cleaned_data["passenger_count"]

            if passengers > vehicle.seat_capacity:

                form.add_error(
                    "passenger_count",
                    f"This vehicle only has {vehicle.seat_capacity} seats."
                )

            else:

                booking = form.save()

                send_booking_confirmation(booking)

                if booking.booking_status == "Confirmed":
                    booking.vehicle.status = "Booked"
                    booking.vehicle.save()

                messages.success(
                    request,
                    "Booking created successfully."
            )

            return redirect("bookings:booking_list")
    else:

        form = BookingForm()

    return render(
        request,
        "bookings/booking_form.html",
        {
            "form": form,
            "title": "Add Booking",
        },
    )


@login_required
def booking_update(request, pk):
    if not staff_only(request):
        messages.error(
            request,
            "You do not have permission to edit bookings."
        )
        return redirect("bookings:customer_bookings")

    booking = get_object_or_404(
        Booking,
        pk=pk,
    )

    if request.method == "POST":

        form = BookingForm(
            request.POST,
            instance=booking,
        )

        if form.is_valid():

            vehicle = form.cleaned_data["vehicle"]

            passengers = form.cleaned_data["passenger_count"]

            if passengers > vehicle.seat_capacity:

                form.add_error(
                    "passenger_count",
                    f"This vehicle only has {vehicle.seat_capacity} seats."
                )

            else:

                booking = form.save()

                if booking.booking_status == "Confirmed":
                    booking.vehicle.status = "Booked"

                elif booking.booking_status in ["Completed", "Cancelled"]:
                    booking.vehicle.status = "Available"

                booking.vehicle.save()

                messages.success(
                request,
                "Booking updated successfully."
                )

                return redirect("bookings:booking_list")

    else:

        form = BookingForm(
            instance=booking
        )

    return render(
        request,
        "bookings/booking_form.html",
        {
            "form": form,
            "title": "Edit Booking",
        },
    )

@login_required
def booking_review(request, pk):
    if not staff_only(request):
        messages.error(
            request,
            "You do not have permission to review bookings."
        )
        return redirect("dashboard")

    booking = get_object_or_404(
        Booking.objects.select_related(
            "customer",
            "vehicle",
            "driver",
        ),
        pk=pk,
    )

    if booking.booking_status != "Pending":
        messages.error(
            request,
            "Only pending bookings can be reviewed."
        )
        return redirect("bookings:booking_list")

    # Available vehicles only
    from apps.vehicles.models import Vehicle

    available_vehicles = Vehicle.objects.filter(
        status="Available"
    ).order_by("vehicle_name")

    # Available drivers only
    from apps.drivers.models import Driver

    available_drivers = Driver.objects.filter(
        status="Available"
    ).order_by("full_name")

    if request.method == "POST":

        form = BookingReviewForm(
            request.POST,
            vehicle_queryset=available_vehicles,
            driver_queryset=available_drivers,
        )

        if form.is_valid():

            action = request.POST.get("action")

            # =========================
            # APPROVE BOOKING
            # =========================
            if action == "approve":

                vehicle = form.cleaned_data["vehicle"]
                driver = form.cleaned_data["driver"]

                old_status = booking.booking_status

                # Assign vehicle and driver
                booking.vehicle = vehicle
                booking.driver = driver
                booking.booking_status = "Confirmed"
                booking.save()

                # Mark vehicle as booked
                vehicle.status = "Booked"
                vehicle.save()

                AuditLog.objects.create(
                    user=request.user,
                    module="Booking",
                    action="APPROVE",
                    booking=booking,
                    customer=booking.customer,
                    description=(
                        f"{request.user.get_full_name() or request.user.username} "
                        f"approved booking {booking.booking_number} for customer "
                        f"{booking.customer.first_name} "
                        f"{booking.customer.last_name}. "
                        f"Booking status changed from "
                        f"{old_status} to Confirmed. "
                        f"Vehicle assigned: "
                        f"{vehicle.vehicle_name} "
                        f"({vehicle.registration_number}). "
                        f"Driver assigned: "
                        f"{driver.full_name}."
                    ),
                    ip_address=request.META.get("REMOTE_ADDR"),
                )

                messages.success(
                    request,
                    f"Booking {booking.booking_number} approved successfully."
                )

                return redirect("bookings:booking_list")

            # =========================
            # REJECT BOOKING
            # =========================
            elif action == "reject":

                old_status = booking.booking_status

                reason = form.cleaned_data["reason"]

                booking.booking_status = "Cancelled"
                booking.save()

                AuditLog.objects.create(
                    user=request.user,
                    module="Booking",
                    action="REJECT",
                    booking=booking,
                    customer=booking.customer,
                    description=(
                        f"{request.user.get_full_name() or request.user.username} "
                        f"rejected booking {booking.booking_number} for customer "
                        f"{booking.customer.first_name} "
                        f"{booking.customer.last_name}. "
                        f"Booking status changed from "
                        f"{old_status} to Cancelled. "
                        f"Reason: "
                        f"{reason if reason else 'No reason provided'}."
                    ),
                    ip_address=request.META.get("REMOTE_ADDR"),
                )

                messages.warning(
                    request,
                    f"Booking {booking.booking_number} rejected."
                )

                return redirect("bookings:booking_list")

    else:

        form = BookingReviewForm(
            vehicle_queryset=available_vehicles,
            driver_queryset=available_drivers,
        )

    return render(
        request,
        "bookings/booking_review.html",
        {
            "booking": booking,
            "form": form,
        },
    )

@login_required
def booking_delete(request, pk):
    if not staff_only(request):
        messages.error(
            request,
            "You do not have permission to delete bookings."
        )
        return redirect("bookings:customer_bookings")

    booking = get_object_or_404(
        Booking,
        pk=pk,
    )

    if request.method == "POST":

        booking.vehicle.status = "Available"
        booking.vehicle.save()

        booking.delete()

        messages.success(
            request,
            "Booking deleted successfully."
        )

        return redirect(
            "bookings:booking_list"
        )

    return render(
        request,
        "bookings/booking_delete.html",
        {
            "booking": booking,
        },
    )

@login_required
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

@login_required
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
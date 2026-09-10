from urllib import request

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Booking
from .forms import BookingForm
from apps.emails.services import send_booking_confirmation


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


def booking_create(request):

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


def booking_update(request, pk):

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


def booking_delete(request, pk):

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
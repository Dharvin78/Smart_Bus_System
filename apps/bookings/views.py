from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Booking
from .forms import BookingForm


def booking_list(request):
    """
    Display all bookings with search and pagination.
    """

    search = request.GET.get("search", "")

    bookings = Booking.objects.select_related(
        "customer",
        "customer__user",
        "vehicle",
        "driver",
    ).order_by("-travel_date")

    if search:
        bookings = bookings.filter(
            Q(booking_number__icontains=search) |
            Q(customer__user__username__icontains=search) |
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

                form.save()

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

                form.save()

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
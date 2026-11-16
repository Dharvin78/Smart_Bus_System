# Create your views here.

from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.utils.dateparse import parse_date

from .models import Driver, DriverReview
from .forms import DriverReviewForm

from apps.bookings.models import Booking
from apps.maintenance.models import Maintenance
from apps.helpdesk.services.data_access import get_customer_for_user
from apps.accounts.decorators import customer_required, driver_required

@customer_required
def driver_review(request, booking_id):
    # Only customers can submit driver reviews
    if request.user.profile.role != "Customer":
        messages.error(
            request,
            "You do not have permission to submit driver reviews."
        )
        return redirect("dashboard")

    # Find the Customer record linked to this login
    customer = get_customer_for_user(request.user)

    # Customer can only access their own completed booking
    booking = get_object_or_404(
        Booking,
        pk=booking_id,
        customer=customer,
        booking_status="Completed",
    )

    # Prevent duplicate reviews
    if DriverReview.objects.filter(booking=booking).exists():
        messages.info(
            request,
            "You have already submitted a review for this booking."
        )
        return redirect("bookings:customer_bookings")

    if request.method == "POST":
        form = DriverReviewForm(request.POST)

        if form.is_valid():
            review = form.save(commit=False)
            review.booking = booking
            review.save()

            messages.success(
                request,
                "Driver review submitted successfully."
            )

            return redirect("bookings:customer_bookings")

    else:
        form = DriverReviewForm()

    return render(
        request,
        "drivers/driver_review.html",
        {
            "form": form,
            "booking": booking,
        }
    )


@driver_required
def driver_calendar(request):
    """
    Display the logged-in driver's trip and maintenance calendar.
    """
    driver = Driver.objects.filter(user=request.user).first()

    return render(
        request,
        "drivers/driver_calendar.html",
        {"driver": driver},
    )


@driver_required
def driver_calendar_events(request):
    """
    Return the logged-in driver's assigned trips and
    maintenance duties as FullCalendar JSON events.
    """
    driver = Driver.objects.filter(user=request.user).first()

    if driver is None:
        return JsonResponse([], safe=False)

    start = parse_date(request.GET.get("start", "")[:10])
    end = parse_date(request.GET.get("end", "")[:10])

    if not start or not end:
        return JsonResponse(
            {"error": "Invalid calendar date range."},
            status=400,
        )

    events = []

    # FullCalendar's end date is exclusive.
    trips = Booking.objects.filter(
        driver=driver,
        booking_status__in=["Confirmed", "Completed"],
        travel_date__lt=end,
    ).filter(
        Q(return_date__gte=start) |
        Q(return_date__isnull=True, travel_date__gte=start)
    ).select_related("vehicle")

    for booking in trips:
        last_day = booking.return_date or booking.travel_date

        if last_day < booking.travel_date:
            last_day = booking.travel_date

        events.append({
            "id": f"trip-{booking.pk}",
            "title": f"Trip: {booking.pickup_location} → {booking.destination}",
            "start": booking.travel_date.isoformat(),
            "end": (last_day + timedelta(days=1)).isoformat(),
            "allDay": True,
            "backgroundColor": "#2563eb",
            "borderColor": "#2563eb",
            "extendedProps": {
                "type": "Trip",
                "status": booking.booking_status,
                "booking_number": booking.booking_number,
                "departure_time": (
                    booking.departure_time.strftime("%H:%M")
                    if booking.departure_time else ""
                ),
                "vehicle": (
                    str(booking.vehicle)
                    if booking.vehicle else "Not assigned"
                ),
            },
        })

    # Assigned maintenance duties
    maintenance_records = Maintenance.objects.filter(
        assigned_driver=driver,
        service_date__gte=start,
        service_date__lt=end,
    ).exclude(
        status="Cancelled"
    ).select_related("vehicle")

    for maintenance in maintenance_records:
        events.append({
            "id": f"maintenance-{maintenance.pk}",
            "title": f"Maintenance: {maintenance.vehicle}",
            "start": maintenance.service_date.isoformat(),
            "allDay": True,
            "backgroundColor": "#f59e0b",
            "borderColor": "#f59e0b",
            "textColor": "#111827",
            "extendedProps": {
                "type": "Maintenance",
                "status": maintenance.status,
                "maintenance_type": maintenance.get_maintenance_type_display(),
                "workshop": maintenance.workshop,
                "remarks": maintenance.remarks or "",
            },
        })

    return JsonResponse(events, safe=False)

from django.shortcuts import render
from django.db.models import Sum, Count, Avg

from apps.bookings.models import Booking
from apps.vehicles.models import Vehicle
from apps.drivers.models import Driver
from apps.payments.models import Payment

from django.utils import timezone



def dashboard(request):

    # Basic counts
    total_bookings = Booking.objects.count()
    total_vehicles = Vehicle.objects.count()
    total_drivers = Driver.objects.count()

    # Aggregate totals
    total_revenue = Payment.objects.aggregate(total=Sum("amount"))["total"] or 0

    # Upcoming bookings (limit 5)
    upcoming_bookings = (
        Booking.objects.filter(booking_status="Confirmed")
        .order_by("travel_date")[:5]
    )

    # Fleet status counts
    available_vehicles = Vehicle.objects.filter(status="Available").count()
    on_trip_vehicles = Vehicle.objects.filter(status="On Trip").count()
    maintenance_vehicles = Vehicle.objects.filter(status="Maintenance").count()

    # Revenue for today and this month (use date-safe filters)
    today = timezone.now().date()
    today_revenue = (
        Payment.objects.filter(payment_date=today).aggregate(total=Sum("amount"))["total"] or 0
    )

    month_revenue = (
        Payment.objects.filter(payment_date__year=today.year, payment_date__month=today.month)
        .aggregate(total=Sum("amount"))["total"] or 0
    )

    # Customer count and average payment
    customer_count = Booking.objects.values("customer").distinct().count()
    average_booking = Payment.objects.aggregate(avg=Avg("amount"))["avg"] or 0

    context = {
        "total_bookings": total_bookings,
        "total_vehicles": total_vehicles,
        "total_drivers": total_drivers,
        "total_revenue": total_revenue,
        "upcoming_bookings": upcoming_bookings,
        "available_vehicles": available_vehicles,
        "on_trip_vehicles": on_trip_vehicles,
        "maintenance_vehicles": maintenance_vehicles,
        "today_revenue": today_revenue,
        "month_revenue": month_revenue,
        "customer_count": customer_count,
        "average_booking": average_booking,
    }

    return render(request, "dashboard/dashboard.html", context)
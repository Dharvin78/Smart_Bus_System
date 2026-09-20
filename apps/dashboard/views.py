from django.shortcuts import render
from django.db.models import Sum, Count, Avg

from apps.bookings.models import Booking
from apps.vehicles.models import Vehicle
from apps.drivers.models import Driver
from apps.payments.models import Payment
from django.db.models.functions import TruncMonth
from decimal import Decimal

from django.utils import timezone



def dashboard(request):

    # ==========================
    # BASIC COUNTS
    # ==========================

    total_bookings = Booking.objects.count()
    total_vehicles = Vehicle.objects.count()
    total_drivers = Driver.objects.count()

    # ==========================
    # REVENUE
    # ==========================

    # Only paid payments are treated as revenue
    total_revenue = (
        Payment.objects
        .filter(payment_status="Paid")
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )

    # ==========================
    # UPCOMING BOOKINGS
    # ==========================

    upcoming_bookings = (
        Booking.objects
        .filter(booking_status="Confirmed")
        .order_by("travel_date")[:5]
    )

    # ==========================
    # FLEET STATUS
    # ==========================

    available_vehicles = Vehicle.objects.filter(
        status="Available"
    ).count()

    on_trip_vehicles = Vehicle.objects.filter(
        status="On Trip"
    ).count()

    maintenance_vehicles = Vehicle.objects.filter(
        status="Maintenance"
    ).count()

    # ==========================
    # DATE
    # ==========================

    today = timezone.now().date()

    # ==========================
    # TODAY REVENUE
    # ==========================

    today_revenue = (
        Payment.objects
        .filter(
            payment_status="Paid",
            payment_date=today
        )
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )

    # ==========================
    # MONTH REVENUE
    # ==========================

    month_revenue = (
        Payment.objects
        .filter(
            payment_status="Paid",
            payment_date__year=today.year,
            payment_date__month=today.month
        )
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )

    # ==========================
    # CUSTOMER COUNT
    # ==========================

    customer_count = (
        Booking.objects
        .values("customer")
        .distinct()
        .count()
    )

    # ==========================
    # AVERAGE PAYMENT
    # ==========================

    average_booking = (
        Payment.objects
        .filter(payment_status="Paid")
        .aggregate(avg=Avg("amount"))["avg"]
        or 0
    )

    # ==========================
    # MONTHLY REVENUE
    # ==========================

    monthly_revenue = (
        Payment.objects
        .filter(payment_status="Paid")
        .annotate(month=TruncMonth("payment_date"))
        .values("month")
        .annotate(
            revenue=Sum("amount")
        )
        .order_by("month")
    )

    revenue_labels = []
    revenue_values = []

    for item in monthly_revenue:

        revenue_labels.append(
            item["month"].strftime("%b %Y")
        )

        revenue_values.append(
            float(item["revenue"] or 0)
        )

    # ==========================
    # REVENUE GROWTH
    # ==========================

    revenue_growth = None

    if len(revenue_values) >= 2:

        previous_revenue = revenue_values[-2]
        current_revenue = revenue_values[-1]

        if previous_revenue > 0:

            revenue_growth = (
                (current_revenue - previous_revenue)
                / previous_revenue
            ) * 100

    # ==========================
    # CONTEXT
    # ==========================

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

        # Revenue analysis
        "revenue_labels": revenue_labels,
        "revenue_values": revenue_values,
        "revenue_growth": revenue_growth,
    }

    return render(
        request,
        "dashboard/dashboard.html",
        context
    )
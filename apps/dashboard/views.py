
from datetime import date, datetime

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Exists, OuterRef, Q, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.bookings.models import Booking
from apps.vehicles.models import Vehicle
from apps.drivers.models import Driver
from apps.payments.models import Payment


# ==========================================================
# OWNER / ADMIN DASHBOARD
# ==========================================================

@login_required
def dashboard(request):

    profile = getattr(request.user, "profile", None)

    if profile is None:
        raise PermissionDenied("User profile not found.")

    if profile.role == "Customer":
        return redirect("customer_dashboard")

    if profile.role == "Driver":
        return redirect("driver_dashboard")

    if profile.role not in ["Owner", "Admin"]:
        raise PermissionDenied("Access denied.")

    today = timezone.localdate()
    now = timezone.localtime()

    # ======================================================
    # BASIC STATISTICS - ALL TIME
    # ======================================================

    total_bookings = Booking.objects.count()
    total_vehicles = Vehicle.objects.count()
    total_drivers = Driver.objects.count()

    # ======================================================
    # BOOKING OVERVIEW - PERIOD FILTER
    # ======================================================

    booking_period = request.GET.get(
        "booking_period", "month"
    )

    valid_periods = ["month", "year", "all"]

    if booking_period not in valid_periods:
        booking_period = "month"

    booking_queryset = Booking.objects.all()

    if booking_period == "month":

        booking_queryset = booking_queryset.filter(
            created_at__year=today.year,
            created_at__month=today.month,
        )

        booking_period_label = "This Month"

    elif booking_period == "year":

        booking_queryset = booking_queryset.filter(
            created_at__year=today.year
        )

        booking_period_label = "This Year"

    else:
        booking_period_label = "All Time"

    booking_counts = booking_queryset.aggregate(
        pending=Count(
            "pk",
            filter=Q(booking_status="Pending")
        ),
        confirmed=Count(
            "pk",
            filter=Q(booking_status="Confirmed")
        ),
        completed=Count(
            "pk",
            filter=Q(booking_status="Completed")
        ),
        cancelled=Count(
            "pk",
            filter=Q(booking_status="Cancelled")
        ),
    )

    period_total_bookings = sum(
        booking_counts.values()
    )

    # ======================================================
    # UPCOMING BOOKINGS
    # ======================================================

    upcoming_bookings = (
        Booking.objects
        .filter(
            booking_status="Confirmed"
        )
        .filter(
            Q(travel_date__gt=today)
            | Q(
                travel_date=today,
                departure_time__gte=now.time().replace(
                    tzinfo=None
                ),
            )
        )
        .select_related(
            "customer",
            "vehicle",
            "driver",
        )
        .order_by(
            "travel_date",
            "departure_time",
        )[:5]
    )

    # ======================================================
    # FLEET STATUS
    # ======================================================

    fleet_counts = Vehicle.objects.aggregate(
        available=Count(
            "pk",
            filter=Q(status="Available")
        ),
        booked=Count(
            "pk",
            filter=Q(status="Booked")
        ),
        on_trip=Count(
            "pk",
            filter=Q(status="On Trip")
        ),
        maintenance=Count(
            "pk",
            filter=Q(status="Maintenance")
        ),
    )

    available_vehicles = fleet_counts["available"]
    booked_vehicles = fleet_counts["booked"]
    on_trip_vehicles = fleet_counts["on_trip"]
    maintenance_vehicles = fleet_counts["maintenance"]

    other_vehicles = max(
        total_vehicles
        - available_vehicles
        - booked_vehicles
        - on_trip_vehicles
        - maintenance_vehicles,
        0,
    )

    # ======================================================
    # DRIVER STATUS
    # ======================================================

    driver_counts = Driver.objects.aggregate(
        available=Count(
            "pk",
            filter=Q(status="Available")
        ),
        reserved=Count(
            "pk",
            filter=Q(status="Reserved")
        ),
        on_trip=Count(
            "pk",
            filter=Q(status="On Trip")
        ),
    )

    # ======================================================
    # PAYMENT OVERVIEW
    # ======================================================

    payment_counts = Payment.objects.aggregate(
        pending=Count(
            "pk",
            filter=Q(payment_status="Pending")
        ),
        paid=Count(
            "pk",
            filter=Q(payment_status="Paid")
        ),
        failed=Count(
            "pk",
            filter=Q(payment_status="Failed")
        ),
        cancelled=Count(
            "pk",
            filter=Q(payment_status="Cancelled")
        ),
    )

    # ======================================================
    # REVENUE
    # ======================================================

    paid_payments_queryset = Payment.objects.filter(
        payment_status="Paid"
    )

    total_revenue = (
        paid_payments_queryset.aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )

    today_revenue = (
        paid_payments_queryset.filter(
            payment_date=today
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )

    month_revenue = (
        paid_payments_queryset.filter(
            payment_date__year=today.year,
            payment_date__month=today.month,
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )

    # ======================================================
    # MONTHLY REVENUE - LAST 6 MONTHS
    # ======================================================

    first_month = today.replace(day=1)
    months = []

    for offset in range(5, -1, -1):

        year = first_month.year
        month = first_month.month - offset

        while month <= 0:
            month += 12
            year -= 1

        months.append(date(year, month, 1))

    monthly_revenue = (
        paid_payments_queryset
        .filter(
            payment_date__gte=months[0],
            payment_date__lte=today,
        )
        .annotate(
            month=TruncMonth("payment_date")
        )
        .values("month")
        .annotate(
            revenue=Sum("amount")
        )
        .order_by("month")
    )

    revenue_by_month = {
        item["month"].strftime("%Y-%m"): float(
            item["revenue"] or 0
        )
        for item in monthly_revenue
        if item["month"] is not None
    }

    revenue_labels = []
    revenue_values = []

    for month in months:

        revenue_labels.append(
            month.strftime("%b %Y")
        )

        revenue_values.append(
            revenue_by_month.get(
                month.strftime("%Y-%m"),
                0,
            )
        )

    # ======================================================
    # REVENUE GROWTH
    # ======================================================

    revenue_growth = None

    if len(revenue_values) >= 2:

        previous_revenue = revenue_values[-2]
        current_revenue = revenue_values[-1]

        if previous_revenue > 0:

            revenue_growth = (
                (current_revenue - previous_revenue)
                / previous_revenue
            ) * 100

    # ======================================================
    # RECENT BOOKINGS
    # ======================================================

    recent_bookings = (
        Booking.objects
        .select_related(
            "customer",
            "vehicle",
            "driver",
        )
        .order_by("-created_at")[:5]
    )

    # ======================================================
    # DASHBOARD CONTEXT
    # ======================================================

    context = {

        # User role
        "user_role": profile.role,
        "is_owner": profile.role == "Owner",
        "is_admin": profile.role == "Admin",

        # Main KPI cards - all time
        "total_bookings": total_bookings,
        "total_vehicles": total_vehicles,
        "total_drivers": total_drivers,

        # Booking overview - selected period
        "booking_period": booking_period,
        "booking_period_label": booking_period_label,
        "period_total_bookings": period_total_bookings,

        "pending_bookings": booking_counts["pending"],
        "confirmed_bookings": booking_counts["confirmed"],
        "completed_bookings": booking_counts["completed"],
        "cancelled_bookings": booking_counts["cancelled"],

        # Bookings
        "upcoming_bookings": upcoming_bookings,
        "recent_bookings": recent_bookings,

        # Fleet status
        "available_vehicles": available_vehicles,
        "booked_vehicles": booked_vehicles,
        "on_trip_vehicles": on_trip_vehicles,
        "maintenance_vehicles": maintenance_vehicles,
        "other_vehicles": other_vehicles,

        # Driver status
        "available_drivers": driver_counts["available"],
        "reserved_drivers": driver_counts["reserved"],
        "on_trip_drivers": driver_counts["on_trip"],

        # Payment overview
        "pending_payments": payment_counts["pending"],
        "paid_payments": payment_counts["paid"],
        "failed_payments": payment_counts["failed"],
        "cancelled_payments": payment_counts["cancelled"],

        # Revenue
        "total_revenue": total_revenue,
        "today_revenue": today_revenue,
        "month_revenue": month_revenue,

        # Revenue analytics
        "revenue_labels": revenue_labels,
        "revenue_values": revenue_values,
        "revenue_growth": revenue_growth,
    }

    return render(
        request,
        "dashboard/dashboard.html",
        context,
    )


# ==========================================================
# CUSTOMER DASHBOARD
# ==========================================================

@login_required
def customer_dashboard(request):

    profile = getattr(request.user, "profile", None)

    if not profile or profile.role != "Customer":
        raise PermissionDenied("Access denied.")

    bookings = (
        Booking.objects
        .filter(customer__user=request.user)
        .order_by("-travel_date")
    )

    now = timezone.now()
    paid_payments = Payment.objects.filter(booking_id=OuterRef("pk"), payment_status="Paid")
    awaiting_payment = list(bookings.filter(
        booking_status="Confirmed", payment_status="Pending", total_price__gt=0,
    ).filter(~Exists(paid_payments)))
    for booking in awaiting_payment:
        booking.payment_due_at = booking.payment_deadline or booking.departure_datetime
        booking.payment_expired = booking.payment_due_at <= now
    awaiting_payment.sort(key=lambda booking: (booking.payment_expired, booking.payment_due_at))

    context = {
        "total_bookings": bookings.count(),

        "pending_bookings": bookings.filter(
            booking_status="Pending"
        ).count(),

        "confirmed_bookings": bookings.filter(
            booking_status="Confirmed"
        ).count(),

        "completed_bookings": bookings.filter(
            booking_status="Completed"
        ).count(),

        "recent_bookings": bookings[:5],
        "awaiting_payment": awaiting_payment,
        "payment_countdown_started_at": now,
    }

    return render(
        request,
        "dashboard/customer_dashboard.html",
        context,
    )


# ==========================================================
# DRIVER DASHBOARD
# ==========================================================

@login_required
def driver_dashboard(request):

    profile = getattr(request.user, "profile", None)

    if not profile or profile.role != "Driver":
        raise PermissionDenied("Access denied.")

    bookings = (
        Booking.objects
        .filter(driver__user=request.user)
        .order_by("travel_date")
    )

    context = {
        "total_trips": bookings.count(),

        "upcoming_trips": bookings.filter(
            booking_status="Confirmed",
            travel_date__gte=timezone.localdate(),
        ),

        "completed_trips": bookings.filter(
            booking_status="Completed"
        ).count(),
    }

    return render(
        request,
        "dashboard/driver_dashboard.html",
        context,
    )

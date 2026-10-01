from django.shortcuts import render
from django.db.models.functions import TruncMonth
from django.db.models import Count,Sum

from apps.bookings.models import Booking
from apps.payments.models import Payment

from apps.analytics.services.business_data import get_business_data
from apps.analytics.services.ai_analysis import generate_business_analysis

def dashboard(request):

    # Monthly Revenue
    monthly_revenue = (
        Payment.objects
        .filter(payment_status="Paid")
        .annotate(month=TruncMonth("payment_date"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )

    # Bookings by Month
    monthly_bookings = (
            Booking.objects
            .annotate(month=TruncMonth("travel_date"))
            .values("month")
            .annotate(total=Count("id"))
            .order_by("month")
        )

    # Revenue by Vehicle
    vehicle_revenue = (
        Payment.objects
        .filter(payment_status="Paid")
        .values("booking__vehicle__vehicle_name")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )

    # Revenue by Driver
    driver_revenue = (
        Payment.objects
        .filter(payment_status="Paid")
        .values("booking__driver__full_name")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )

    # Top Customers
    top_customers = (
        Payment.objects
        .filter(payment_status="Paid")
        .values(
            "booking__customer__first_name",
            "booking__customer__last_name"
        )
        .annotate(
            total_spent=Sum("amount"),
            booking_count=Count("booking")
        )
        .order_by("-total_spent")[:10]
    )

    # Popular Routes
    popular_routes = (
        Booking.objects
        .values(
            "pickup_location",
            "destination"
        )
        .annotate(
            total=Count("id")
        )
        .order_by("-total")[:10]
    )

    # Payment Method Distribution
    payment_methods = (
        Payment.objects
        .values("payment_method")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    # Booking Status Distribution
    booking_status = (
        Booking.objects
        .values("booking_status")
        .annotate(total=Count("id"))
        .order_by("booking_status")
    )

    labels = []
    revenue = []

    booking_labels = []
    booking_totals = []

    vehicle_labels = []
    vehicle_totals = []

    driver_labels = []
    driver_totals = []

    customer_labels = []
    customer_totals = []

    route_labels = []
    route_totals = []

    payment_labels = []
    payment_totals = []

    status_labels = []
    status_totals = []

    for item in monthly_revenue:
        labels.append(item["month"].strftime("%b %Y"))
        revenue.append(float(item["total"]))

    for item in monthly_bookings:
        booking_labels.append(item["month"].strftime("%b %Y"))
        booking_totals.append(item["total"])

    for item in vehicle_revenue:
        vehicle_labels.append(item["booking__vehicle__vehicle_name"])
        vehicle_totals.append(float(item["total"]))

    for item in driver_revenue:
        driver_labels.append(item["booking__driver__full_name"])
        driver_totals.append(float(item["total"]))

    for customer in top_customers:

        full_name = (
            f"{customer['booking__customer__first_name']} "
            f"{customer['booking__customer__last_name']}"
        )

        customer_labels.append(full_name)
        customer_totals.append(float(customer["total_spent"]))

    for route in popular_routes:

        route_name = (
            f"{route['pickup_location']} → {route['destination']}"
        )

        route_labels.append(route_name)
        route_totals.append(route["total"])

    for payment in payment_methods:

        payment_labels.append(payment["payment_method"])
        payment_totals.append(payment["total"])

    for status in booking_status:

        status_labels.append(status["booking_status"])
        status_totals.append(status["total"])

    # ==========================
    # DYNAMIC AI BUSINESS ANALYSIS
    # ==========================

    business_data = get_business_data()

    ai_insights = generate_business_analysis(
        business_data
    )

    context = {
        "labels": labels,
        "revenue": revenue,
        "booking_labels": booking_labels,
        "booking_totals": booking_totals,
        "vehicle_labels": vehicle_labels,
        "vehicle_totals": vehicle_totals,
        "driver_labels": driver_labels,
        "driver_totals": driver_totals,
        "customer_labels": customer_labels,
        "customer_totals": customer_totals,
        "route_labels": route_labels,
        "route_totals": route_totals,
        "payment_labels": payment_labels,
        "payment_totals": payment_totals,
        "status_labels": status_labels,
        "status_totals": status_totals,
        "ai_insights": ai_insights,
    }

    return render(
        request,
        "analytics/dashboard.html",
        context,
    )

    context = {
        "labels": labels,
        "revenue": revenue,

        "booking_labels": booking_labels,
        "booking_totals": booking_totals,

        "vehicle_labels": vehicle_labels,
        "vehicle_totals": vehicle_totals,

        "driver_labels": driver_labels,
        "driver_totals": driver_totals,

        "customer_labels": customer_labels,
        "customer_totals": customer_totals,

        "route_labels": route_labels,
        "route_totals": route_totals,

        "payment_labels": payment_labels,
        "payment_totals": payment_totals,

        "status_labels": status_labels,
        "status_totals": status_totals,

        "ai_insights": ai_insights,
    }

    return render(
        request,
        "analytics/dashboard.html",
        context,
    )
from django.shortcuts import render
from django.db.models.functions import TruncMonth
from django.db.models import Count,Sum

from apps.bookings.models import Booking
from apps.payments.models import Payment


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
    # AI BUSINESS INSIGHTS
    # ==========================

    ai_insights = []

    # Revenue
    if len(revenue) >= 2:

        last_month = revenue[-2]
        current_month = revenue[-1]

        if last_month > 0:

            growth = ((current_month - last_month) / last_month) * 100

            if growth > 0:

                ai_insights.append(
                    f"📈 Revenue increased by {growth:.1f}% compared to last month."
                )

            elif growth < 0:

                ai_insights.append(
                    f"📉 Revenue decreased by {abs(growth):.1f}% compared to last month."
                )

            else:

                ai_insights.append(
                    "Revenue remained stable compared to last month."
                )

    if vehicle_revenue.exists():

        best_vehicle = vehicle_revenue.first()

        ai_insights.append(

            f"🚌 Highest earning vehicle: "

            f"{best_vehicle['booking__vehicle__vehicle_name']} "

            f"(RM {best_vehicle['total']:.2f})"

        )

    if driver_revenue.exists():

        best_driver = driver_revenue.first()

        ai_insights.append(

            f"👨‍✈️ Best performing driver: "

            f"{best_driver['booking__driver__full_name']} "

        )

    if top_customers.exists():

        customer = top_customers.first()

        ai_insights.append(

            f"👥 Top customer: "

            f"{customer['booking__customer__first_name']} "

            f"{customer['booking__customer__last_name']}"

        )

    if popular_routes.exists():

        route = popular_routes.first()

        ai_insights.append(

            f"🗺️ Most popular route: "

            f"{route['pickup_location']} → "

            f"{route['destination']}"

        )

    if payment_methods.exists():

        method = payment_methods.first()

        ai_insights.append(

            f"💳 Preferred payment method: "

            f"{method['payment_method']}"

        )

    pending = Booking.objects.filter(
        booking_status="Pending"
    ).count()

    if pending > 0:

        ai_insights.append(

            f"⚠️ {pending} pending booking(s) require confirmation."

        )

    if popular_routes.exists():

        ai_insights.append(

            "💡 Recommendation: Increase vehicle availability "

            "on the most popular route during weekends."

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
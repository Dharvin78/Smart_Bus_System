from django.db.models import Count, Sum, Avg
from django.db.models.functions import TruncMonth

from apps.bookings.models import Booking
from apps.payments.models import Payment
from apps.vehicles.models import Vehicle
from apps.drivers.models import Driver
from apps.maintenance.models import Maintenance
from apps.fuel.models import Fuel


def get_business_data():

    # ==========================
    # REVENUE
    # ==========================

    monthly_revenue = (
        Payment.objects
        .filter(payment_status="Paid")
        .annotate(month=TruncMonth("payment_date"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )

    revenue_data = [
        {
            "month": item["month"].strftime("%b %Y"),
            "amount": float(item["total"] or 0),
        }
        for item in monthly_revenue
        if item["month"]
    ]

    total_revenue = (
        Payment.objects
        .filter(payment_status="Paid")
        .aggregate(total=Sum("amount"))["total"] or 0
    )

    # ==========================
    # BOOKINGS
    # ==========================

    total_bookings = Booking.objects.count()

    completed_bookings = Booking.objects.filter(
        booking_status="Completed"
    ).count()

    confirmed_bookings = Booking.objects.filter(
        booking_status="Confirmed"
    ).count()

    pending_bookings = Booking.objects.filter(
        booking_status="Pending"
    ).count()

    cancelled_bookings = Booking.objects.filter(
        booking_status="Cancelled"
    ).count()

    monthly_bookings = (
        Booking.objects
        .annotate(month=TruncMonth("travel_date"))
        .values("month")
        .annotate(total=Count("id"))
        .order_by("month")
    )

    booking_trend = [
        {
            "month": item["month"].strftime("%b %Y"),
            "bookings": item["total"],
        }
        for item in monthly_bookings
        if item["month"]
    ]

    # ==========================
    # PASSENGER DEMAND
    # ==========================

    passenger_summary = Booking.objects.aggregate(
        total_passengers=Sum("passenger_count"),
        average_passengers=Avg("passenger_count"),
    )

    # ==========================
    # VEHICLES
    # ==========================

    total_vehicles = Vehicle.objects.count()

    available_vehicles = Vehicle.objects.filter(
        status="Available"
    ).count()

    booked_vehicles = Vehicle.objects.filter(
        status="Booked"
    ).count()

    maintenance_vehicles = Vehicle.objects.filter(
        status="Maintenance"
    ).count()

    inactive_vehicles = Vehicle.objects.filter(
        status="Inactive"
    ).count()

    total_seat_capacity = (
        Vehicle.objects.aggregate(
            total=Sum("seat_capacity")
        )["total"] or 0
    )

    vehicle_types = (
        Vehicle.objects
        .values("bus_type")
        .annotate(
            count=Count("id"),
            capacity=Sum("seat_capacity"),
        )
        .order_by("-count")
    )

    vehicle_data = [
        {
            "bus_type": item["bus_type"],
            "count": item["count"],
            "seat_capacity": item["capacity"] or 0,
        }
        for item in vehicle_types
    ]

    # ==========================
    # DRIVERS
    # ==========================

    total_drivers = Driver.objects.count()

    available_drivers = Driver.objects.filter(
        status="Available"
    ).count()

    on_trip_drivers = Driver.objects.filter(
        status="On Trip"
    ).count()

    inactive_drivers = Driver.objects.filter(
        status="Inactive"
    ).count()

    driver_performance = (
        Booking.objects
        .filter(
            booking_status="Completed",
            driver__isnull=False,
        )
        .values(
            "driver__full_name"
        )
        .annotate(
            completed_trips=Count("id"),
            revenue=Sum("total_price"),
        )
        .order_by("-completed_trips")
    )

    driver_data = [
        {
            "driver": item["driver__full_name"],
            "completed_trips": item["completed_trips"],
            "revenue": float(item["revenue"] or 0),
        }
        for item in driver_performance
    ]

    # ==========================
    # ROUTES
    # ==========================

    popular_routes = (
        Booking.objects
        .values(
            "pickup_location",
            "destination",
        )
        .annotate(
            bookings=Count("id"),
        )
        .order_by("-bookings")[:10]
    )

    route_data = [
        {
            "route": (
                f"{item['pickup_location']} → "
                f"{item['destination']}"
            ),
            "bookings": item["bookings"],
        }
        for item in popular_routes
    ]

    # ==========================
    # MAINTENANCE
    # ==========================

    maintenance_summary = Maintenance.objects.aggregate(
        total_records=Count("id"),
        total_cost=Sum("cost"),
    )

    maintenance_by_vehicle = (
        Maintenance.objects
        .values("vehicle__vehicle_name")
        .annotate(
            records=Count("id"),
            cost=Sum("cost"),
        )
        .order_by("-cost")[:10]
    )

    maintenance_data = [
        {
            "vehicle": item["vehicle__vehicle_name"],
            "records": item["records"],
            "cost": float(item["cost"] or 0),
        }
        for item in maintenance_by_vehicle
    ]

    # ==========================
    # FUEL
    # ==========================

    fuel_summary = Fuel.objects.aggregate(
        total_litres=Sum("litres"),
        total_cost=Sum("total_cost"),
        average_price=Avg("price_per_litre"),
        total_refills=Count("id"),
    )

    # ==========================
    # PAYMENT
    # ==========================

    payment_methods = (
        Payment.objects
        .values("payment_method")
        .annotate(
            transactions=Count("id"),
            amount=Sum("amount"),
        )
        .order_by("-transactions")
    )

    payment_data = [
        {
            "method": item["payment_method"],
            "transactions": item["transactions"],
            "amount": float(item["amount"] or 0),
        }
        for item in payment_methods
    ]

    # ==========================
    # FINAL BUSINESS DATA
    # ==========================

    return {
        "revenue": {
            "total": float(total_revenue),
            "monthly": revenue_data,
        },

        "bookings": {
            "total": total_bookings,
            "completed": completed_bookings,
            "confirmed": confirmed_bookings,
            "pending": pending_bookings,
            "cancelled": cancelled_bookings,
            "monthly": booking_trend,
            "total_passengers": passenger_summary["total_passengers"] or 0,
            "average_passengers": float(
                passenger_summary["average_passengers"] or 0
            ),
        },

        "vehicles": {
            "total": total_vehicles,
            "available": available_vehicles,
            "booked": booked_vehicles,
            "maintenance": maintenance_vehicles,
            "inactive": inactive_vehicles,
            "total_seat_capacity": total_seat_capacity,
            "by_type": vehicle_data,
        },

        "drivers": {
            "total": total_drivers,
            "available": available_drivers,
            "on_trip": on_trip_drivers,
            "inactive": inactive_drivers,
            "performance": driver_data,
        },

        "routes": route_data,

        "maintenance": {
            "total_records": maintenance_summary["total_records"] or 0,
            "total_cost": float(
                maintenance_summary["total_cost"] or 0
            ),
            "by_vehicle": maintenance_data,
        },

        "fuel": {
            "total_litres": float(
                fuel_summary["total_litres"] or 0
            ),
            "total_cost": float(
                fuel_summary["total_cost"] or 0
            ),
            "average_price": float(
                fuel_summary["average_price"] or 0
            ),
            "total_refills": fuel_summary["total_refills"] or 0,
        },

        "payments": {
            "methods": payment_data,
        },
    }
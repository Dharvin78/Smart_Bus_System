from django.utils import timezone

from apps.bookings.models import Booking
from apps.customers.models import Customer
from apps.drivers.models import Driver
from apps.payments.models import Payment
from apps.vehicles.models import Vehicle
from apps.maintenance.models import Maintenance
from apps.fuel.models import Fuel


def get_customer_for_user(user):
    """
    Find the Customer record belonging to the logged-in user
    using the user's email address.
    """

    if not user.is_authenticated:
        return None

    if not user.email:
        return None

    return Customer.objects.filter(
        email__iexact=user.email
    ).first()


def get_driver_for_user(user):
    """
    Find the Driver record belonging to the logged-in user
    using the user's email address.
    """

    if not user.is_authenticated:
        return None

    if not user.email:
        return None

    return Driver.objects.filter(
        email__iexact=user.email
    ).first()


# ============================================================
# CUSTOMER DATA
# ============================================================

def get_customer_bookings(user):
    """
    Return only bookings belonging to the logged-in customer.
    """

    customer = get_customer_for_user(user)

    if not customer:
        return []

    bookings = Booking.objects.filter(
        customer=customer
    ).select_related(
        "vehicle",
        "driver",
    )

    return list(
        bookings.values(
            "booking_number",
            "pickup_location",
            "destination",
            "travel_date",
            "departure_time",
            "return_date",
            "passenger_count",
            "total_price",
            "booking_status",
            "payment_status",
        )
    )


def get_customer_payments(user):
    """
    Return only payments associated with the logged-in
    customer's bookings.
    """

    customer = get_customer_for_user(user)

    if not customer:
        return []

    payments = Payment.objects.filter(
        booking__customer=customer
    ).select_related(
        "booking"
    )

    return list(
        payments.values(
            "booking__booking_number",
            "amount",
            "payment_method",
            "payment_status",
            "transaction_id",
            "payment_date",
            "remarks",
        )
    )


def get_customer_upcoming_bookings(user):
    """
    Return the logged-in customer's upcoming bookings.
    """

    customer = get_customer_for_user(user)

    if not customer:
        return []

    today = timezone.localdate()

    bookings = Booking.objects.filter(
        customer=customer,
        travel_date__gte=today,
    ).exclude(
        booking_status="Cancelled"
    ).order_by(
        "travel_date",
        "departure_time",
    )

    return list(
        bookings.values(
            "booking_number",
            "pickup_location",
            "destination",
            "travel_date",
            "departure_time",
            "vehicle__vehicle_name",
            "driver__full_name",
            "booking_status",
            "payment_status",
        )
    )


# ============================================================
# DRIVER DATA
# ============================================================

def get_driver_bookings(user):
    """
    Return bookings assigned to the logged-in driver.
    """

    driver = get_driver_for_user(user)

    if not driver:
        return []

    bookings = Booking.objects.filter(
        driver=driver
    ).select_related(
        "vehicle",
        "customer",
    )

    return list(
        bookings.values(
            "booking_number",
            "pickup_location",
            "destination",
            "travel_date",
            "departure_time",
            "return_date",
            "passenger_count",
            "booking_status",
            "vehicle__vehicle_name",
            "vehicle__registration_number",
        )
    )


def get_driver_upcoming_trips(user):
    """
    Return upcoming trips assigned to the logged-in driver.
    """

    driver = get_driver_for_user(user)

    if not driver:
        return []

    today = timezone.localdate()

    bookings = Booking.objects.filter(
        driver=driver,
        travel_date__gte=today,
    ).exclude(
        booking_status="Cancelled"
    ).order_by(
        "travel_date",
        "departure_time",
    )

    return list(
        bookings.values(
            "booking_number",
            "pickup_location",
            "destination",
            "travel_date",
            "departure_time",
            "passenger_count",
            "booking_status",
            "vehicle__vehicle_name",
            "vehicle__registration_number",
        )
    )


def get_driver_vehicle(user):
    """
    Return the vehicle currently assigned to the logged-in driver.
    """

    driver = get_driver_for_user(user)

    if not driver or not driver.assigned_vehicle:
        return None

    vehicle = driver.assigned_vehicle

    return {
        "vehicle_name": vehicle.vehicle_name,
        "registration_number": vehicle.registration_number,
        "bus_type": vehicle.bus_type,
        "seat_capacity": vehicle.seat_capacity,
        "manufacture_year": vehicle.manufacture_year,
        "status": vehicle.status,
        "insurance_expiry": vehicle.insurance_expiry,
        "road_tax_expiry": vehicle.road_tax_expiry,
    }


# ============================================================
# ADMIN / OWNER DATA
# ============================================================

def get_vehicle_information():
    """
    Return general vehicle information for authorized
    administrative users.
    """

    return list(
        Vehicle.objects.all().values(
            "registration_number",
            "vehicle_name",
            "bus_type",
            "seat_capacity",
            "manufacture_year",
            "insurance_expiry",
            "road_tax_expiry",
            "status",
        )
    )


def get_driver_information():
    """
    Return operational driver information.
    """

    return list(
        Driver.objects.all().values(
            "full_name",
            "phone",
            "email",
            "driving_license",
            "license_expiry",
            "status",
            "assigned_vehicle__vehicle_name",
            "assigned_vehicle__registration_number",
        )
    )


def get_booking_information():
    """
    Return general booking information for authorized
    administrative users.
    """

    return list(
        Booking.objects.all().values(
            "booking_number",
            "pickup_location",
            "destination",
            "travel_date",
            "departure_time",
            "passenger_count",
            "total_price",
            "booking_status",
            "payment_status",
        )
    )


def get_maintenance_information():
    """
    Return maintenance information for authorized users.
    """

    return list(
        Maintenance.objects.all().values(
            "vehicle__vehicle_name",
            "vehicle__registration_number",
            "maintenance_type",
            "workshop",
            "service_date",
            "next_service_date",
            "mileage",
            "cost",
            "status",
            "needs_maintenance",
            "remarks",
        )
    )


def get_fuel_information():
    """
    Return fuel information for authorized users.
    """

    return list(
        Fuel.objects.all().values(
            "vehicle__vehicle_name",
            "vehicle__registration_number",
            "fuel_type",
            "refill_date",
            "litres",
            "price_per_litre",
            "total_cost",
            "fuel_station",
            "mileage",
            "remarks",
        )
    )


def get_revenue_information():
    """
    Return paid payment information for authorized
    administrative users.
    """

    return list(
        Payment.objects.filter(
            payment_status="Paid"
        ).values(
            "booking__booking_number",
            "amount",
            "payment_method",
            "payment_date",
        )
    )
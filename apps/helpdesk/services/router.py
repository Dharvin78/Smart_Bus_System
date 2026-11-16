
from .permissions import user_has_permission

from .data_access import (
    get_customer_bookings,
    get_customer_payments,
    get_customer_upcoming_bookings,
    get_driver_bookings,
    get_driver_upcoming_trips,
    get_driver_vehicle,
    get_vehicle_information,
    get_driver_information,
    get_booking_information,
    get_maintenance_information,
    get_fuel_information,
    get_revenue_information,
)

from .context import get_previous_context


def contains_any(text, phrases):
    return any(phrase in text for phrase in phrases)


def detect_intent(message, role="Customer"):
    text = " ".join(message.lower().split())

    # Emotional support
    if contains_any(text, [
        "feeling down",
        "feel sad",
        "feeling sad",
        "i'm sad",
        "i am sad",
        "feeling lonely",
        "feel lonely",
        "feeling stressed",
        "feel stressed",
        "feeling anxious",
        "i'm upset",
    ]):
        return "general_help"

    # Personal trip schedule takes priority over generic trips
    if contains_any(text, [
        "next trip",
        "upcoming trip",
        "next booking",
        "upcoming booking",
        "next assigned trip",
        "upcoming assigned trip",
    ]):
        return "upcoming_trip"

    # Driver's own vehicle
    if contains_any(text, [
        "my vehicle",
        "my bus",
        "assigned vehicle",
        "assigned bus",
    ]):
        return "assigned_vehicle"

    # Personal payments
    if contains_any(text, [
        "my payment",
        "my payments",
        "payment for my booking",
        "did i pay",
        "have i paid",
        "my transaction",
    ]):
        return "own_payments"

    # Personal bookings or assigned trips
    if contains_any(text, [
        "my booking",
        "my bookings",
        "my trip",
        "my trips",
        "my reservation",
        "my reservations",
        "assigned trips",
        "assigned bookings",
    ]):
        return "own_bookings"

    # Personal driver information is not an all-driver query
    if contains_any(text, [
        "my driver",
        "driver for my",
        "who is driving my",
    ]):
        if role == "Customer":
            return "own_bookings"
        if role == "Driver":
            return "own_bookings"

    # Maintenance
    if contains_any(text, [
        "maintenance",
        "servicing",
        "repair",
        "workshop",
    ]):
        return "maintenance_information"

    # Fuel
    if contains_any(text, [
        "fuel",
        "diesel",
        "petrol",
        "refuel",
    ]):
        return "fuel_information"

    # Revenue
    if contains_any(text, [
        "revenue",
        "income",
        "earnings",
        "sales report",
    ]):
        return "revenue_information"

    # All-driver information
    if contains_any(text, [
        "all drivers",
        "driver list",
        "driver information",
        "drivers",
    ]):
        return "driver_information"

    # Vehicle information
    if contains_any(text, [
        "all vehicles",
        "vehicle list",
        "vehicle information",
        "fleet",
        "buses",
        "vehicles",
    ]):
        return "vehicle_information"

    # General booking administration
    if contains_any(text, [
        "all bookings",
        "booking list",
        "booking information",
        "reservations",
        "bookings",
    ]):
        return "booking_information"

    return "general_help"


def is_follow_up_question(message):
    text = " ".join(message.lower().split())

    phrases = [
        "what about",
        "how about",
        "the first one",
        "the second one",
        "the next one",
        "the previous one",
        "that one",
        "that booking",
        "that payment",
        "that bus",
        "that vehicle",
        "is it paid",
        "when is it",
        "where is it",
        "who is driving",
        "who is the driver",
    ]

    return contains_any(text, phrases)


def get_data_for_question(user, message, conversation=None):
    role = getattr(
        getattr(user, "profile", None),
        "role",
        "Customer",
    )

    intent = detect_intent(message, role)

    # Follow-ups may reuse a previous database intent.
    # Never inherit a general conversation intent.
    if (
        conversation
        and intent == "general_help"
        and is_follow_up_question(message)
    ):
        previous = get_previous_context(conversation) or {}
        previous_intent = previous.get("category")

        database_intents = {
            "own_bookings",
            "own_payments",
            "upcoming_trip",
            "assigned_vehicle",
            "vehicle_information",
            "driver_information",
            "booking_information",
            "maintenance_information",
            "fuel_information",
            "revenue_information",
        }

        if previous_intent in database_intents:
            intent = previous_intent

    if intent == "own_bookings":
        permission = (
            "assigned_trips"
            if role == "Driver"
            else "own_bookings"
        )

    elif intent == "upcoming_trip":
        if role == "Driver":
            permission = "assigned_trips"
        elif role == "Customer":
            permission = "own_bookings"
        else:
            permission = "booking_information"

    else:
        permission = {
            "own_payments": "own_payments",
            "assigned_vehicle": "assigned_vehicle",
            "vehicle_information": "vehicle_information",
            "driver_information": "driver_information",
            "booking_information": "booking_information",
            "maintenance_information": "maintenance_information",
            "fuel_information": "fuel_information",
            "revenue_information": "revenue_information",
            "general_help": "general_help",
        }.get(intent, "general_help")

    if not user_has_permission(user, permission):
        return {
            "allowed": False,
            "intent": intent,
            "data": None,
            "message": (
                "You do not have permission to access "
                "this information."
            ),
        }

    if intent == "own_bookings":
        if role == "Driver":
            data = get_driver_bookings(user)
        else:
            data = get_customer_bookings(user)

    elif intent == "own_payments":
        data = get_customer_payments(user)

    elif intent == "upcoming_trip":
        if role == "Driver":
            data = get_driver_upcoming_trips(user)
        elif role == "Customer":
            data = get_customer_upcoming_bookings(user)
        else:
            data = get_booking_information()

    elif intent == "assigned_vehicle":
        data = get_driver_vehicle(user)

    elif intent == "vehicle_information":
        data = get_vehicle_information(user)

    elif intent == "driver_information":
        data = get_driver_information(user)

    elif intent == "booking_information":
        data = get_booking_information(user)

    elif intent == "maintenance_information":
        data = get_maintenance_information(user)

    elif intent == "fuel_information":
        data = get_fuel_information(user)

    elif intent == "revenue_information":
        data = get_revenue_information(user)

    else:
        data = None

    return {
        "allowed": True,
        "intent": intent,
        "data": data,
        "message": None,
    }

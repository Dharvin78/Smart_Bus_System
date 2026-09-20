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

from .context import (
    is_follow_up_question,
    get_previous_context,
)


def detect_intent(message):
    """
    Detect the general intent of a Help Assistant question.
    """

    text = message.lower()

    # Customer booking questions
    if any(keyword in text for keyword in [
        "my booking",
        "my bookings",
        "my trip",
        "my trips",
        "my reservation",
        "my reservations",
    ]):
        return "own_bookings"

    # Customer payment questions
    if any(keyword in text for keyword in [
        "my payment",
        "my payments",
        "payment for my booking",
        "did i pay",
        "have i paid",
        "my transaction",
    ]):
        return "own_payments"

    # Upcoming trip questions
    if any(keyword in text for keyword in [
        "next trip",
        "upcoming trip",
        "next booking",
        "upcoming booking",
    ]):
        return "upcoming_trip"

    # Assigned vehicle
    if any(keyword in text for keyword in [
        "my vehicle",
        "my bus",
        "assigned vehicle",
        "assigned bus",
    ]):
        return "assigned_vehicle"

    # Vehicle information
    if any(keyword in text for keyword in [
        "vehicle",
        "vehicles",
        "bus",
        "buses",
    ]):
        return "vehicle_information"

    # Driver information
    if any(keyword in text for keyword in [
        "driver",
        "drivers",
    ]):
        return "driver_information"

    # Booking information
    if any(keyword in text for keyword in [
        "booking",
        "bookings",
        "reservation",
        "reservations",
    ]):
        return "booking_information"

    # Maintenance
    if any(keyword in text for keyword in [
        "maintenance",
        "service",
        "servicing",
        "repair",
    ]):
        return "maintenance_information"

    # Fuel
    if any(keyword in text for keyword in [
        "fuel",
        "diesel",
        "petrol",
        "refuel",
        "refilling",
    ]):
        return "fuel_information"

    # Revenue
    if any(keyword in text for keyword in [
        "revenue",
        "income",
        "sales",
        "earnings",
    ]):
        return "revenue_information"

    return "general_help"

def is_follow_up_question(message):
    """
    Detect questions that commonly depend on previous
    conversation context.
    """

    text = message.lower().strip()

    follow_up_phrases = [
        "what about",
        "how about",
        "which one",
        "which is",
        "what is the second",
        "what is the first",
        "what about the second",
        "what about the first",
        "the second one",
        "the first one",
        "the next one",
        "the previous one",
        "that one",
        "that booking",
        "that payment",
        "that bus",
        "that vehicle",
        "that driver",
        "is it paid",
        "when is it",
        "where is it",
        "who is the driver",
        "who is driving",
    ]

    return any(
        phrase in text
        for phrase in follow_up_phrases
    )

def get_follow_up_intent(conversation):
    """
    Determine the previous meaningful intent from the
    conversation history.
    """

    if not conversation:
        return None

    analyses = conversation.question_analysis.order_by(
        "-created_at"
    )

    for analysis in analyses:
        if analysis.category:
            return analysis.category

    return None

def get_data_for_question(user, message, conversation=None):
    intent = detect_intent(message)

    # Resolve follow-up questions using previous context
        # Resolve follow-up questions using conversation context
    if (
        conversation
        and is_follow_up_question(message)
    ):
        previous_context = get_previous_context(conversation)

        previous_category = previous_context["category"]

        if previous_category:
            intent = previous_category

    role = getattr(getattr(user, "profile", None), "role", "Customer")

    # Role-aware permission mapping
    if intent == "own_bookings":
        if role == "Driver":
            required_permission = "assigned_trips"
        else:
            required_permission = "own_bookings"

    elif intent == "upcoming_trip":
        if role == "Driver":
            required_permission = "assigned_trips"
        elif role == "Customer":
            required_permission = "own_bookings"
        else:
            required_permission = "booking_information"

    else:
        required_permission = {
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

    # Check permission
    if not user_has_permission(user, required_permission):
        return {
            "allowed": False,
            "intent": intent,
            "data": None,
            "message": "You do not have permission to access this information.",
        }

    # Retrieve the appropriate data
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
        data = get_vehicle_information()

    elif intent == "driver_information":
        data = get_driver_information()

    elif intent == "booking_information":
        data = get_booking_information()

    elif intent == "maintenance_information":
        data = get_maintenance_information()

    elif intent == "fuel_information":
        data = get_fuel_information()

    elif intent == "revenue_information":
        data = get_revenue_information()

    else:
        data = None

    return {
        "allowed": True,
        "intent": intent,
        "data": data,
        "message": None,
    }
from apps.helpdesk.models import Conversation

# ============================================================
# ROLE PERMISSIONS
# ============================================================

ROLE_PERMISSIONS = {

    "Owner": {
        "general_help",
        "own_account",
        "own_bookings",
        "own_payments",
        "driver_information",
        "vehicle_information",
        "booking_information",
        "customer_information",
        "maintenance_information",
        "fuel_information",
        "revenue_information",
        "reports_information",
        "business_information",
        "system_information",
    },

    "Admin": {
        "general_help",
        "own_account",
        "booking_information",
        "customer_information",
        "driver_information",
        "vehicle_information",
        "maintenance_information",
        "fuel_information",
        "revenue_information",
        "reports_information",
        "system_information",
    },

    "Driver": {
        "general_help",
        "own_account",
        "own_bookings",
        "assigned_trips",
        "assigned_vehicle",
        "driver_information",
        "system_information",
    },

    "Customer": {
        "general_help",
        "own_account",
        "own_bookings",
        "own_payments",
        "system_information",
    },
}


def get_user_role(user):
    """
    Return the role of the currently authenticated user.
    """

    profile = getattr(user, "profile", None)

    if profile:
        return profile.role

    return "Customer"


def user_has_permission(user, permission):
    """
    Check whether the current user has a specific
    Help Assistant permission.
    """

    role = get_user_role(user)

    allowed_permissions = ROLE_PERMISSIONS.get(
        role,
        set()
    )

    return permission in allowed_permissions


def get_allowed_permissions(user):
    """
    Return all permissions available to the current user.
    """

    role = get_user_role(user)

    return ROLE_PERMISSIONS.get(
        role,
        set()
    )

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(allowed_roles):
    """
    Restrict access based on UserProfile role.

    Examples:
        @role_required(["Owner"])
        @role_required(["Owner", "Admin"])
        @role_required(["Customer"])
        @role_required(["Driver"])
    """

    def decorator(view_func):

        @login_required(login_url="accounts:login")
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            profile = getattr(request.user, "profile", None)

            if profile is None:
                raise PermissionDenied(
                    "User profile not found."
                )

            if profile.role not in allowed_roles:
                raise PermissionDenied(
                    "You do not have permission to access this page."
                )

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def admin_required(view_func):
    return role_required(["Owner", "Admin"])(view_func)


def customer_required(view_func):
    return role_required(["Customer"])(view_func)


def driver_required(view_func):
    return role_required(["Driver"])(view_func)

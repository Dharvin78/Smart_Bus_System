from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from .models import UserProfile


def role_required(allowed_roles):
    """
    Restrict access based on UserProfile role.

    Example:
        @role_required(["Owner"])
        @role_required(["Owner", "Admin"])
    """

    def decorator(view_func):

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            if not request.user.is_authenticated:
                return redirect("accounts:login")

            try:
                role = request.user.profile.role
            except UserProfile.DoesNotExist:
                messages.error(
                    request,
                    "User profile not found."
                )
                return redirect("accounts:login")

            if role not in allowed_roles:
                messages.error(
                    request,
                    "You do not have permission to access this page."
                )
                return redirect("dashboard:dashboard")

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
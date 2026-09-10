# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.db.models import Q
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils.crypto import get_random_string

from .models import UserProfile
from .forms import (SignupForm, ProfileForm, CustomPasswordChangeForm, ManageUserForm,)
from .decorators import role_required

def login_view(request):

    if request.user.is_authenticated:
        return redirect("dashboard")
    
    if request.method == "POST":

        username = request.POST.get("username")

        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user:

            login(request, user)

            if hasattr(user, "profile") and user.profile.must_change_password:
                messages.warning(
                    request,
                    "You must change your temporary password before continuing."
                )
                return redirect("accounts:change_password")

            messages.success(
                request,
                "Login successful."
            )

            return redirect("dashboard")

        messages.error(
            request,
            "Invalid username or password."
        )

    return render(
        request,
        "accounts/login.html"
    )

def signup_view(request):

    if request.method == "POST":

        form = SignupForm(request.POST)

        if form.is_valid():

            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"]
            )

            # UserProfile is automatically created by signals.py

            login(request, user)

            messages.success(
                request,
                "Registration successful."
            )

            return redirect("dashboard")

    else:

        form = SignupForm()

    return render(
        request,
        "accounts/signup.html",
        {
            "form": form
        }
    )


def logout_view(request):

    logout(request)

    return redirect("accounts:login")

@login_required
def profile(request):

    return render(
        request,
        "accounts/profile.html",
    )

def edit_profile(request):

    profile = request.user.profile

    if request.method == "POST":

        form = ProfileForm(
            request.POST,
            request.FILES,
            instance=profile,
            user=request.user
        )

        if form.is_valid():

            form.save(user=request.user)

            messages.success(
                request,
                "Profile updated successfully."
            )

            return redirect("accounts:profile")

    else:

        form = ProfileForm(
            instance=profile,
            user=request.user
        )

    return render(
        request,
        "accounts/edit_profile.html",
        {
            "form": form
        }
    )

@login_required
def change_password(request):
    if request.method == "POST":
        form = CustomPasswordChangeForm(
            request.user,
            request.POST
        )

        if form.is_valid():
            user = form.save()

            # Mark temporary password as changed
            if hasattr(user, "profile"):
                user.profile.must_change_password = False
                user.profile.save(
                    update_fields=["must_change_password"]
                )

            messages.success(
                request,
                "Your password has been changed successfully."
            )

            return redirect("dashboard")

    else:
        form = CustomPasswordChangeForm(request.user)

    return render(
        request,
        "accounts/change_password.html",
        {
            "form": form,
            "force_change": getattr(
                request.user.profile,
                "must_change_password",
                False
            ),
        }
    )

@login_required
def user_list(request):

    current_role = request.user.profile.role

    # ---------------------------------
    # Permission
    # ---------------------------------
    if current_role not in [
        UserProfile.OWNER,
        UserProfile.ADMIN,
    ]:
        messages.error(
            request,
            "You do not have permission to access user management."
        )
        return redirect("dashboard")

    # ---------------------------------
    # Roles this user is allowed to see
    # ---------------------------------
    if current_role == UserProfile.OWNER:
        allowed_roles = [
            UserProfile.OWNER,
            UserProfile.ADMIN,
            UserProfile.DRIVER,
            UserProfile.CUSTOMER,
        ]
    else:
        allowed_roles = [
            UserProfile.DRIVER,
            UserProfile.CUSTOMER,
        ]

    # ---------------------------------
    # Filter
    # ---------------------------------
    user_type = request.GET.get("type", "all").lower()

    if user_type == "staff":

        filter_roles = [
            role for role in [
                UserProfile.OWNER,
                UserProfile.ADMIN,
                UserProfile.DRIVER,
            ]
            if role in allowed_roles
        ]

    elif user_type == "customers":

        filter_roles = [UserProfile.CUSTOMER]

    else:

        user_type = "all"
        filter_roles = allowed_roles

    # ---------------------------------
    # Users
    # ---------------------------------
    users = (
        User.objects
        .select_related("profile")
        .filter(profile__role__in=filter_roles)
        .order_by("username")
    )

    # ---------------------------------
    # Search
    # ---------------------------------
    search = request.GET.get("search", "").strip()

    if search:

        users = users.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )

    # ---------------------------------
    # Counts
    # ---------------------------------
    all_count = (
        User.objects
        .filter(profile__role__in=allowed_roles)
        .count()
    )

    staff_count = (
        User.objects
        .filter(
            profile__role__in=[
                role for role in [
                    UserProfile.OWNER,
                    UserProfile.ADMIN,
                    UserProfile.DRIVER,
                ]
                if role in allowed_roles
            ]
        )
        .count()
    )

    customer_count = (
        User.objects
        .filter(
            profile__role=UserProfile.CUSTOMER
        )
        .count()
    )

    # ---------------------------------
    # Pagination
    # ---------------------------------
    paginator = Paginator(users, 10)

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "accounts/user_list.html",
        {
            "users": page_obj,
            "page_obj": page_obj,
            "search": search,
            "role": current_role,
            "user_type": user_type,

            "all_count": all_count,
            "staff_count": staff_count,
            "customer_count": customer_count,

            "is_paginated": page_obj.has_other_pages(),
        }
    )

@login_required
def user_create(request):
    current_role = request.user.profile.role

    # Only Owner and Admin can create users
    if current_role not in [UserProfile.OWNER, UserProfile.ADMIN]:
        messages.error(
            request,
            "You do not have permission to create users."
        )
        return redirect("dashboard")

    if request.method == "POST":
        form = ManageUserForm(
            request.POST,
            user=request.user
        )

        if form.is_valid():

            # Generate temporary password
            temporary_password = get_random_string(
                length=12
            )

            user = form.save(commit=False)

            # Set secure hashed password
            user.set_password(temporary_password)

            user.save()

            # Create/update profile
            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    "role": form.cleaned_data["role"],
                    "phone": form.cleaned_data["phone"],
                    "must_change_password": True,
                }
            )

            # Login URL
            login_url = request.build_absolute_uri(
                reverse("accounts:login")
            )

            # Email content
            subject = "Smart Bus Management System - Account Created"

            message = f"""
Hello {user.first_name or user.username},

Your account has been created for the Smart Bus Management System.

Account Details
----------------
Username: {user.username}
Temporary Password: {temporary_password}
Role: {form.cleaned_data["role"]}

Login here:
{login_url}

IMPORTANT:
This is a temporary password.

You will be required to change your password when you first log in.

Please do not share your login credentials with anyone.

Regards,
Smart Bus Management System
"""

            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )

                messages.success(
                    request,
                    f"User '{user.username}' created successfully. "
                    "Login credentials have been sent to their email."
                )

            except Exception:
                # Remove account if email could not be sent
                user.delete()

                messages.error(
                    request,
                    "The account could not be created because "
                    "the email could not be sent. Please check "
                    "your email configuration."
                )

                return redirect("accounts:user_create")

            return redirect("accounts:user_list")

    else:
        form = ManageUserForm(user=request.user)

    return render(
        request,
        "accounts/user_form.html",
        {
            "form": form,
            "title": "Add User",
            "role": current_role,
        }
    )

@login_required
def user_update(request, pk):
    current_role = request.user.profile.role

    if current_role not in [UserProfile.OWNER, UserProfile.ADMIN]:
        messages.error(
            request,
            "You do not have permission to edit users."
        )
        return redirect("dashboard")

    target_user = get_object_or_404(
        User.objects.select_related("profile"),
        pk=pk
    )

    target_role = target_user.profile.role

    # Admin restrictions
    if current_role == UserProfile.ADMIN:
        if target_role not in [
            UserProfile.DRIVER,
            UserProfile.CUSTOMER
        ]:
            messages.error(
                request,
                "Admins can only manage Drivers and Customers."
            )
            return redirect("accounts:user_list")

    if request.method == "POST":
        form = ManageUserForm(
            request.POST,
            instance=target_user,
            profile=target_user.profile,
            user=request.user
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                f"User '{target_user.username}' updated successfully."
            )

            return redirect("accounts:user_list")

    else:
        form = ManageUserForm(
            instance=target_user,
            profile=target_user.profile,
            user=request.user
        )

    return render(
        request,
        "accounts/user_form.html",
        {
            "form": form,
            "title": "Edit User",
            "role": current_role,
            "editing_user": target_user,
        }
    )

@login_required
def user_delete(request, pk):

    current_role = request.user.profile.role

    target_user = get_object_or_404(
        User.objects.select_related("profile"),
        pk=pk
    )

    target_role = target_user.profile.role

    if current_role == UserProfile.OWNER:

        allowed_roles = [
            UserProfile.OWNER,
            UserProfile.ADMIN,
            UserProfile.DRIVER,
            UserProfile.CUSTOMER,
        ]

    elif current_role == UserProfile.ADMIN:

        allowed_roles = [
            UserProfile.DRIVER,
            UserProfile.CUSTOMER,
        ]

    else:

        messages.error(
            request,
            "You do not have permission to delete users."
        )

        return redirect("dashboard")

    if target_role not in allowed_roles:

        messages.error(
            request,
            "You do not have permission to delete this user."
        )

        return redirect("accounts:user_list")

    # Prevent deleting yourself
    if target_user == request.user:

        messages.error(
            request,
            "You cannot delete your own account."
        )

        return redirect("accounts:user_list")

    if request.method == "POST":

        target_user.delete()

        messages.success(
            request,
            "User deleted successfully."
        )

        return redirect("accounts:user_list")

    return render(
        request,
        "accounts/user_delete.html",
        {
            "target_user": target_user,
        }
    )
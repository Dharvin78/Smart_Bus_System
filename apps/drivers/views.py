# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required

from .models import Driver
from .forms import DriverForm

from .forms import DriverReviewForm
from .models import DriverReview
from apps.bookings.models import Booking
from apps.helpdesk.services.data_access import get_customer_for_user


def driver_list(request):

    search = request.GET.get("search", "").strip()

    drivers = Driver.objects.all()

    if search:
        drivers = drivers.filter(
            Q(full_name__icontains=search) |
            Q(phone__icontains=search) |
            Q(driving_license__icontains=search)
        )

    drivers = drivers.order_by("full_name")

    paginator = Paginator(drivers, 10)

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "drivers/driver_list.html",
        {
            "page_obj": page_obj,
            "search": search,
        }
    )


def driver_create(request):

    if request.method == "POST":

        form = DriverForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            messages.success(request, "Driver added successfully.")
            return redirect("drivers:driver_list")

    else:
        form = DriverForm()

    return render(request, "drivers/driver_form.html", {
        "form": form,
        "title": "Add Driver"
    })


def driver_update(request, pk):

    driver = get_object_or_404(Driver, pk=pk)

    if request.method == "POST":

        form = DriverForm(
            request.POST,
            request.FILES,
            instance=driver
        )

        if form.is_valid():
            form.save()
            messages.success(request, "Driver updated successfully.")
            return redirect("drivers:driver_list")

    else:
        form = DriverForm(instance=driver)

    return render(request, "drivers/driver_form.html", {
        "form": form,
        "title": "Edit Driver"
    })


def driver_delete(request, pk):

    driver = get_object_or_404(Driver, pk=pk)

    if request.method == "POST":
        driver.delete()
        messages.success(request, "Driver deleted successfully.")
        return redirect("drivers:driver_list")

    return render(request, "drivers/driver_delete.html", {
        "driver": driver
    })

@login_required
def driver_review(request, booking_id):
    # Only customers can submit driver reviews
    if request.user.profile.role != "Customer":
        messages.error(
            request,
            "You do not have permission to submit driver reviews."
        )
        return redirect("dashboard")

    # Find the Customer record linked to this login
    customer = get_customer_for_user(request.user)

    if not customer:
        messages.error(
            request,
            "No customer profile is associated with your account."
        )
        return redirect("dashboard")

    # Customer can only access their own completed booking
    booking = get_object_or_404(
        Booking,
        pk=booking_id,
        customer=customer,
        booking_status="Completed",
    )

    # Prevent duplicate reviews
    if DriverReview.objects.filter(booking=booking).exists():
        messages.info(
            request,
            "You have already submitted a review for this booking."
        )
        return redirect("bookings:customer_bookings")

    if request.method == "POST":
        form = DriverReviewForm(request.POST)

        if form.is_valid():
            review = form.save(commit=False)
            review.booking = booking
            review.save()

            messages.success(
                request,
                "Driver review submitted successfully."
            )

            return redirect("bookings:customer_bookings")

    else:
        form = DriverReviewForm()

    return render(
        request,
        "drivers/driver_review.html",
        {
            "form": form,
            "booking": booking,
        }
    )
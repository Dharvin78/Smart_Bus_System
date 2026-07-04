# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Driver
from .forms import DriverForm


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

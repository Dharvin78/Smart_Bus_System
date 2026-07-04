# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Vehicle
from .forms import VehicleForm


def vehicle_list(request):
    """
    Display all vehicles with search and pagination.
    """

    search = request.GET.get("search", "")

    vehicles = Vehicle.objects.all().order_by("registration_number")

    if search:
        vehicles = vehicles.filter(
            Q(registration_number__icontains=search) |
            Q(vehicle_name__icontains=search)
        )

    paginator = Paginator(vehicles, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "search": search,
    }

    return render(request, "vehicles/vehicle_list.html", context)


def vehicle_create(request):

    if request.method == "POST":
        form = VehicleForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            messages.success(request, "Vehicle added successfully.")
            return redirect("vehicles:vehicle_list")

    else:
        form = VehicleForm()

    return render(request, "vehicles/vehicle_form.html", {
        "form": form,
        "title": "Add Vehicle"
    })


def vehicle_update(request, pk):

    vehicle = get_object_or_404(Vehicle, pk=pk)

    if request.method == "POST":
        form = VehicleForm(
            request.POST,
            request.FILES,
            instance=vehicle
        )

        if form.is_valid():
            form.save()
            messages.success(request, "Vehicle updated successfully.")
            return redirect("vehicles:vehicle_list")

    else:
        form = VehicleForm(instance=vehicle)

    return render(request, "vehicles/vehicle_form.html", {
        "form": form,
        "title": "Edit Vehicle"
    })


def vehicle_delete(request, pk):

    vehicle = get_object_or_404(Vehicle, pk=pk)

    if request.method == "POST":
        vehicle.delete()
        messages.success(request, "Vehicle deleted successfully.")
        return redirect("vehicles:vehicle_list")

    return render(request, "vehicles/vehicle_delete.html", {
        "vehicle": vehicle
    })
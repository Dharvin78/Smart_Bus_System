# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Maintenance
from .forms import MaintenanceForm


def maintenance_list(request):
    """
    Display all maintenance records with search and pagination.
    """

    search = request.GET.get("search", "")

    maintenances = Maintenance.objects.select_related(
        "vehicle"
    ).order_by("-service_date")

    if search:
        maintenances = maintenances.filter(
            Q(vehicle__registration_number__icontains=search) |
            Q(vehicle__vehicle_name__icontains=search) |
            Q(workshop__icontains=search) |
            Q(maintenance_type__icontains=search)
        )

    paginator = Paginator(maintenances, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "maintenances": page_obj,
        "search": search,
        "is_paginated": page_obj.has_other_pages(),
    }

    return render(
        request,
        "maintenance/maintenance_list.html",
        context,
    )


def maintenance_create(request):

    if request.method == "POST":

        form = MaintenanceForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Maintenance record added successfully."
            )

            return redirect("maintenance:maintenance_list")

    else:

        form = MaintenanceForm()

    return render(
        request,
        "maintenance/maintenance_form.html",
        {
            "form": form,
            "title": "Add Maintenance",
        },
    )


def maintenance_update(request, pk):

    maintenance = get_object_or_404(
        Maintenance,
        pk=pk,
    )

    if request.method == "POST":

        form = MaintenanceForm(
            request.POST,
            instance=maintenance,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Maintenance record updated successfully."
            )

            return redirect("maintenance:maintenance_list")

    else:

        form = MaintenanceForm(
            instance=maintenance,
        )

    return render(
        request,
        "maintenance/maintenance_form.html",
        {
            "form": form,
            "title": "Edit Maintenance",
        },
    )


def maintenance_delete(request, pk):

    maintenance = get_object_or_404(
        Maintenance,
        pk=pk,
    )

    if request.method == "POST":

        maintenance.delete()

        messages.success(
            request,
            "Maintenance record deleted successfully."
        )

        return redirect("maintenance:maintenance_list")

    return render(
        request,
        "maintenance/maintenance_delete.html",
        {
            "maintenance": maintenance,
        },
    )
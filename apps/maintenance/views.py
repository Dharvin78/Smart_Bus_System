# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Maintenance
from .forms import MaintenanceForm
from apps.accounts.decorators import admin_required
from apps.drivers.models import Driver
from django.db import transaction, OperationalError
from django.db.models import F

@admin_required
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



@admin_required
def maintenance_create(request):

    if request.method == "POST":
        form = MaintenanceForm(request.POST)

        try:
            with transaction.atomic():

                # Acquire a SQLite write lock before
                # validating booking and maintenance conflicts.
                from apps.vehicles.models import Vehicle

                Vehicle.objects.filter(
                    pk=request.POST.get("vehicle")
                ).update(
                    status=F("status")
                )

                if form.is_valid():
                    form.save()

                    messages.success(
                        request,
                        "Maintenance record added successfully."
                    )

                    return redirect(
                        "maintenance:maintenance_list"
                    )

        except OperationalError:
            messages.error(
                request,
                "The database is busy. Please try again."
            )

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


@admin_required
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

        try:
            with transaction.atomic():

                # Acquire SQLite write lock before
                # validating scheduling conflicts.
                Maintenance.objects.filter(
                    pk=pk
                ).update(
                    status=F("status")
                )

                # Validate booking and maintenance conflicts.
                if form.is_valid():

                    form.save()

                    messages.success(
                        request,
                        "Maintenance record updated successfully."
                    )

                    return redirect(
                        "maintenance:maintenance_list"
                    )

        except OperationalError:
            messages.error(
                request,
                "The database is busy. Please try again."
            )

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

@admin_required
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
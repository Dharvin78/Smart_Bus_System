# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Fuel
from .forms import FuelForm


def fuel_list(request):

    search = request.GET.get("search", "")

    fuels = Fuel.objects.select_related(
        "vehicle"
    ).order_by("-refill_date")

    if search:

        fuels = fuels.filter(

            Q(vehicle__registration_number__icontains=search) |
            Q(fuel_station__icontains=search) |
            Q(fuel_type__icontains=search)

        )

    paginator = Paginator(fuels, 10)

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

    return render(

        request,

        "fuel/fuel_list.html",

        {
            "page_obj": page_obj,
            "fuels": page_obj,
            "search": search,
            "is_paginated": page_obj.has_other_pages(),
        }

    )


def fuel_create(request):

    if request.method == "POST":

        form = FuelForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Fuel record added successfully."
            )

            return redirect("fuel:fuel_list")

    else:

        form = FuelForm()

    return render(

        request,

        "fuel/fuel_form.html",

        {
            "form": form,
            "title": "Add Fuel Record",
        }

    )


def fuel_update(request, pk):

    fuel = get_object_or_404(
        Fuel,
        pk=pk,
    )

    if request.method == "POST":

        form = FuelForm(
            request.POST,
            instance=fuel,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Fuel record updated successfully."
            )

            return redirect("fuel:fuel_list")

    else:

        form = FuelForm(
            instance=fuel,
        )

    return render(

        request,

        "fuel/fuel_form.html",

        {
            "form": form,
            "title": "Edit Fuel Record",
        }

    )


def fuel_delete(request, pk):

    fuel = get_object_or_404(
        Fuel,
        pk=pk,
    )

    if request.method == "POST":

        fuel.delete()

        messages.success(
            request,
            "Fuel record deleted successfully."
        )

        return redirect("fuel:fuel_list")

    return render(

        request,

        "fuel/fuel_delete.html",

        {
            "fuel": fuel,
        }

    )
# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Customer
from .forms import CustomerForm


def customer_list(request):

    search = request.GET.get("search", "")

    customers = Customer.objects.all().order_by("first_name")

    if search:

        customers = customers.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search)
        )

    paginator = Paginator(customers, 10)

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "customers/customer_list.html",
        {
            "customers": page_obj,
            "page_obj": page_obj,
            "search": search,
            "is_paginated": page_obj.has_other_pages(),
        },
    )


def customer_create(request):

    if request.method == "POST":

        form = CustomerForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Customer added successfully."
            )

            return redirect("customers:customer_list")

    else:

        form = CustomerForm()

    return render(
        request,
        "customers/customer_form.html",
        {
            "form": form,
            "title": "Add Customer",
        },
    )


def customer_update(request, pk):

    customer = get_object_or_404(
        Customer,
        pk=pk,
    )

    if request.method == "POST":

        form = CustomerForm(
            request.POST,
            request.FILES,
            instance=customer,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Customer updated successfully."
            )

            return redirect("customers:customer_list")

    else:

        form = CustomerForm(
            instance=customer
        )

    return render(
        request,
        "customers/customer_form.html",
        {
            "form": form,
            "title": "Edit Customer",
        },
    )


def customer_delete(request, pk):

    customer = get_object_or_404(
        Customer,
        pk=pk,
    )

    if request.method == "POST":

        customer.delete()

        messages.success(
            request,
            "Customer deleted successfully."
        )

        return redirect(
            "customers:customer_list"
        )

    return render(
        request,
        "customers/customer_delete.html",
        {
            "customer": customer,
        },
    )
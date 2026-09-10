# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import FileResponse

from .models import Payment
from .forms import PaymentForm
from apps.emails.services import send_payment_receipt
from apps.accounts.decorators import role_required
from django.contrib.auth.decorators import login_required
from .pdf import generate_payment_receipt

@login_required
def payment_list(request):
    """
    Display all payments with search and pagination.
    """

    role = request.user.profile.role

    payments = Payment.objects.select_related(
        "booking",
        "booking__customer"
    ).order_by("-payment_date")

    # Role-based data Acess Control
    if role == "customer":

        payments = payments.filter(
            booking__customer=request.user.profile.user
        )
    elif role in ["Owner", "Admin"]:

        payments = payments

    else:

        # Driver and other roles no Access to payments
        payments = payments.none()

    search = request.GET.get("search", "").strip()

    if search:
        payments = payments.filter(
            Q(booking__booking_number__icontains=search) |
            Q(booking__customer__first_name__icontains=search) |
            Q(booking__customer__last_name__icontains=search) |
            Q(transaction_id__icontains=search)
        )

    #Pagination

    paginator = Paginator(payments, 10)

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "payments": page_obj,
        "search": search,
        "is_paginated": page_obj.has_other_pages(),
        "role": role,
    }

    return render(
        request,
        "payments/payment_list.html",
        context,
    )

@login_required
@role_required(["Owner", "Admin"])
def payment_create(request):

    if request.method == "POST":

        form = PaymentForm(request.POST)

        if form.is_valid():

            payment = form.save()

            send_payment_receipt(payment)

            # Automatically update booking payment status
            payment.booking.payment_status = payment.payment_status
            payment.booking.save()

            messages.success(
                request,
                "Payment added successfully."
            )

            return redirect("payments:payment_list")

    else:

        form = PaymentForm()

    return render(
        request,
        "payments/payment_form.html",
        {
            "form": form,
            "title": "Add Payment",
        },
    )

@login_required
@role_required(["Owner", "Admin"])
def payment_update(request, pk):

    payment = get_object_or_404(
        Payment,
        pk=pk,
    )

    if request.method == "POST":

        form = PaymentForm(
            request.POST,
            instance=payment,
        )

        if form.is_valid():

            payment = form.save()

            payment.booking.payment_status = payment.payment_status
            payment.booking.save()

            messages.success(
                request,
                "Payment updated successfully."
            )

            return redirect("payments:payment_list")

    else:

        form = PaymentForm(
            instance=payment
        )

    return render(
        request,
        "payments/payment_form.html",
        {
            "form": form,
            "title": "Edit Payment",
        },
    )

@login_required
@role_required(["Owner", "Admin"])
def payment_delete(request, pk):

    payment = get_object_or_404(
        Payment,
        pk=pk,
    )

    if request.method == "POST":

        payment.delete()

        messages.success(
            request,
            "Payment deleted successfully."
        )

        return redirect(
            "payments:payment_list"
        )

    return render(
        request,
        "payments/payment_delete.html",
        {
            "payment": payment,
        },
    )

@login_required
def payment_receipt(request, pk):

    role = request.user.profile.role

    if role == "customer":

        payment = get_object_or_404(
            Payment,
            pk=pk,
            booking__customer__user=request.user
        )

    elif role in ["Owner", "Admin"]:

        payment = get_object_or_404(
            Payment,
            pk=pk
        )

    else:

        messages.error(
            request,
            "You do not have permission to access this receipt."
        )

        return redirect("dashboard:dashboard")

    #payment = get_object_or_404(Payment, pk=pk)

    pdf = generate_payment_receipt(payment)

    return FileResponse(
        pdf,
        as_attachment=True,
        filename=f"Receipt_{payment.booking.booking_number}.pdf",
    )


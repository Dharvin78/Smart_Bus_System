# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import FileResponse

from .models import Payment
from .forms import PaymentForm, CustomerPaymentForm
from apps.emails.services import send_payment_receipt
from apps.accounts.decorators import role_required
from django.contrib.auth.decorators import login_required
from .pdf import generate_payment_receipt
from django.utils import timezone
from apps.bookings.models import Booking
from apps.helpdesk.services.data_access import get_customer_for_user

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
    if role == "Customer":

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
def payment_approve(request, pk):

    payment = get_object_or_404(
        Payment,
        pk=pk,
        approval_status="Pending",
    )

    if request.method == "POST":

        payment.approval_status = "Approved"
        payment.approved_by = request.user
        payment.approved_at = timezone.now()
        payment.save()

        messages.success(
            request,
            f"Payment #{payment.id} approved successfully."
        )

        return redirect("payments:payment_list")

    return render(
        request,
        "payments/payment_approve.html",
        {
            "payment": payment,
        },
    )

@login_required
@role_required(["Owner", "Admin"])
def payment_reject(request, pk):

    payment = get_object_or_404(
        Payment,
        pk=pk,
        approval_status="Pending",
    )

    if request.method == "POST":

        payment.approval_status = "Rejected"
        payment.approved_by = request.user
        payment.approved_at = timezone.now()
        payment.save()

        messages.warning(
            request,
            f"Payment #{payment.id} rejected."
        )

        return redirect("payments:payment_list")

    return render(
        request,
        "payments/payment_reject.html",
        {
            "payment": payment,
        },
    )

@login_required
def payment_create(request):

    role = request.user.profile.role

    # Only Owner/Admin or Customer can access payment creation
    if role not in ["Owner", "Admin", "Customer"]:
        messages.error(
            request,
            "You do not have permission to make payments."
        )
        return redirect("dashboard")

    # CUSTOMER PAYMENT FLOW
    if role == "Customer":

        customer = get_customer_for_user(request.user)

        if not customer:
            messages.error(
                request,
                "No customer profile is associated with your account."
            )
            return redirect("dashboard")

        booking_id = request.GET.get("booking")

        if not booking_id:
            messages.error(
                request,
                "No booking was selected for payment."
            )
            return redirect("payments:payment_list")

        booking = get_object_or_404(
            Booking,
            pk=booking_id,
            customer=customer,
        )

        # Find the customer's pending payment
        payment = Payment.objects.filter(
            booking=booking,
            approval_status="Approved",
            payment_status__in=["Pending", "Partially Paid"],
        ).first()

        if not payment:
            messages.error(
                request,
                "This booking has not been approved for payment."
            )
            return redirect("payments:payment_list")

        if request.method == "POST":

            form = CustomerPaymentForm(
                request.POST,
                instance=payment,
            )

            if form.is_valid():

                payment = form.save(commit=False)

                # Customer cannot change these values
                payment.booking = booking
                payment.approval_status = "Approved"

                # Payment becomes paid only after customer submits payment
                payment.payment_status = "Paid"

                payment.save()

                payment.booking.payment_status = "Paid"
                payment.booking.save()

                send_payment_receipt(payment)

                messages.success(
                    request,
                    "Payment completed successfully."
                )

                return redirect(
                    "payments:payment_list"
                )

        else:

            form = CustomerPaymentForm(
                instance=payment
            )

        return render(
            request,
            "payments/payment_form.html",
            {
                "form": form,
                "title": "Make Payment",
            },
        )

    # OWNER / ADMIN PAYMENT FLOW
    if request.method == "POST":

        form = PaymentForm(request.POST)

        if form.is_valid():

            payment = form.save(commit=False)

            payment.approval_status = "Pending"
            payment.payment_status = "Pending"

            payment.save()

            messages.success(
                request,
                "Payment request created and is waiting for approval."
            )

            return redirect(
                "payments:payment_list"
            )

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


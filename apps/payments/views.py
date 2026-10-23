from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import FileResponse
from django.contrib.auth.decorators import login_required
import uuid

from .models import Payment
from .forms import CustomerPaymentForm
from .pdf import generate_payment_receipt
from apps.bookings.models import Booking
from apps.helpdesk.services.data_access import get_customer_for_user
from apps.emails.services import send_payment_receipt
from django.utils import timezone
from django.db import transaction
from apps.accounts.decorators import role_required, customer_required
from .services import process_simulated_payment, PaymentProcessingError

@role_required(["Owner", "Admin", "Customer"])
def payment_list(request):
    role = request.user.profile.role

    payments = Payment.objects.select_related(
        "booking",
        "booking__customer",
    ).order_by("-payment_date")

    if role == "Customer":
        customer = get_customer_for_user(request.user)

        if not customer:
            payments = payments.none()
        else:
            payments = payments.filter(booking__customer=customer)

    elif role not in ["Owner", "Admin"]:
        messages.error(request, "You do not have permission to view payments.")
        return redirect("dashboard")

    search = request.GET.get("search", "").strip()

    if search:
        payments = payments.filter(
            Q(booking__booking_number__icontains=search)
            | Q(booking__customer__first_name__icontains=search)
            | Q(booking__customer__last_name__icontains=search)
            | Q(transaction_id__icontains=search)
        )

    paginator = Paginator(payments, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "payments/payment_list.html",
        {
            "page_obj": page_obj,
            "payments": page_obj,
            "search": search,
            "is_paginated": page_obj.has_other_pages(),
            "role": role,
        },
    )


@customer_required
def payment_create(request):
    customer = get_customer_for_user(request.user)

    if not customer:
        messages.error(request, "Customer profile not found.")
        return redirect("dashboard")

    booking_id = (
        request.POST.get("booking_id")
        if request.method == "POST"
        else request.GET.get("booking")
    )

    if not booking_id:
        messages.error(request, "Please select a booking.")
        return redirect("bookings:customer_bookings")

    booking = get_object_or_404(
        Booking,
        pk=booking_id,
        customer=customer,
    )

    if (
        booking.booking_status != "Confirmed"
        or booking.payment_status == "Paid"
        or Payment.objects.filter(
            booking=booking,
            payment_status="Paid",
        ).exists()
    ):
        messages.error(request, "This booking is not available for payment.")
        return redirect("bookings:customer_bookings")

    if booking.total_price is None or booking.total_price <= 0:
        messages.error(request, "Invalid booking amount.")
        return redirect("bookings:customer_bookings")

    form = CustomerPaymentForm(
        request.POST if request.method == "POST" else None
    )

    if request.method == "POST":
        result = request.POST.get("simulation_result")

        if result not in {"success", "failure"}:
            messages.error(request, "Invalid payment request.")

        elif form.is_valid():
            if result == "failure":
                messages.error(
                    request,
                    "Simulated payment failed. Please try again."
                )
            else:
                try:
                    payment = process_simulated_payment(
                        booking,
                        customer,
                        form.cleaned_data["payment_method"],
                    )
                except PaymentProcessingError as exc:
                    messages.error(request, str(exc))
                    return redirect("bookings:customer_bookings")
                except OperationalError:
                    messages.error(
                        request,
                        "Payment is temporarily unavailable. Please try again."
                    )
                    return redirect("bookings:customer_bookings")

                try:
                    send_payment_receipt(payment)
                except Exception:
                    import logging
                    logging.getLogger(__name__).exception(
                        "Receipt email failed for payment %s",
                        payment.pk,
                    )
                    messages.warning(
                        request,
                        "Payment successful, but the receipt email could not be sent."
                    )
                else:
                    messages.success(
                        request,
                        "Payment successful. Your receipt has been emailed."
                    )

                return redirect("payments:payment_list")

        else:
            messages.error(request, "Please select a valid payment method.")

    return render(
        request,
        "payments/payment_form.html",
        {
            "form": form,
            "title": "Complete Your Payment",
            "booking": booking,
        },
    )

@login_required
def payment_receipt(request, pk):
    role = request.user.profile.role

    if role == "Customer":
        customer = get_customer_for_user(request.user)

        if not customer:
            messages.error(
                request,
                "No customer profile is associated with your account.",
            )
            return redirect("dashboard")

        payment = get_object_or_404(
            Payment.objects.select_related("booking", "booking__customer"),
            pk=pk,
            booking__customer=customer,
        )

    elif role in ["Owner", "Admin"]:
        payment = get_object_or_404(
            Payment.objects.select_related("booking", "booking__customer"),
            pk=pk,
        )

    else:
        messages.error(
            request,
            "You do not have permission to access this receipt.",
        )
        return redirect("dashboard")

    pdf = generate_payment_receipt(payment)

    return FileResponse(
        pdf,
        as_attachment=True,
        filename=f"Receipt_{payment.booking.booking_number}.pdf",
    )
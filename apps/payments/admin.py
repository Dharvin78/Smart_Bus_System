from django.contrib import admin, messages
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.audit.models import AuditLog
from apps.bookings.models import Booking

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    actions = ("record_issued_refunds",)

    list_display = (
        "booking",
        "amount",
        "payment_method",
        "payment_status",
        "payment_date",
        "refund_amount",
        "refund_date",
    )

    list_filter = (
        "payment_status",
        "payment_method",
        "payment_date",
        "booking__refund_status",
    )

    search_fields = (
        "booking__booking_number",
        "transaction_id",
        "booking__customer__first_name",
        "booking__customer__last_name",
    )

    ordering = (
        "-payment_date",
    )

    @admin.action(description="Mark selected refunds as issued externally", permissions=["change"])
    def record_issued_refunds(self, request, queryset):
        recorded = 0
        selections = list(queryset.values_list("pk", "booking_id"))
        for payment_id, booking_id in selections:
            with transaction.atomic():
                Booking.objects.filter(pk=booking_id).update(updated_at=F("updated_at"))
                booking = Booking.objects.filter(pk=booking_id, refund_status="Pending").first()
                if booking is None:
                    continue
                payment = booking.payments.filter(
                    pk=payment_id, refund_amount__gt=0, refund_date__isnull=True,
                    payment_status__in=["Paid", "Partially Paid"],
                ).first()
                if payment is None:
                    continue

                payment.payment_status = (
                    "Refunded" if payment.refund_amount == payment.amount else "Partially Refunded"
                )
                payment.refund_date = timezone.now()
                payment.save(update_fields=["payment_status", "refund_date", "updated_at"])
                if not booking.payments.filter(refund_amount__gt=0, refund_date__isnull=True).exists():
                    booking.refund_status = "Partially Refunded" if booking.cancellation_charge else "Refunded"
                    if booking.refund_status == "Refunded":
                        booking.payment_status = "Refunded"
                    booking.save(update_fields=["payment_status", "refund_status", "updated_at"])

                AuditLog.objects.create(
                    user=request.user, booking=booking, customer=booking.customer,
                    module="Payment", action="REFUND",
                    description=f"Recorded an external refund of RM {payment.refund_amount:.2f} for payment {payment.pk}.",
                    ip_address=request.META.get("REMOTE_ADDR"),
                )
                recorded += 1

        if recorded:
            self.message_user(request, f"Recorded {recorded} issued refund(s).", messages.SUCCESS)
        else:
            self.message_user(request, "No pending refunds were selected.", messages.WARNING)

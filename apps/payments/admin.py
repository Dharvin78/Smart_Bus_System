# Register your models here.
from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):

    list_display = (
        "booking",
        "amount",
        "payment_method",
        "payment_status",
        "payment_date",
    )

    list_filter = (
        "payment_status",
        "payment_method",
        "payment_date",
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
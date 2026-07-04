# Register your models here.
from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):

    list_display = (
        "booking_number",
        "customer",
        "vehicle",
        "driver",
        "travel_date",
        "booking_status",
        "payment_status",
    )

    list_filter = (
        "booking_status",
        "payment_status",
        "travel_date",
    )

    search_fields = (
        "booking_number",
        "customer__user__username",
        "vehicle__registration_number",
        "driver__full_name",
    )

    ordering = (
        "-travel_date",
    )

# Register your models here.
from django.contrib import admin
from .models import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        "registration_number",
        "vehicle_name",
        "bus_type",
        "seat_capacity",
        "status",
        "insurance_expiry",
        "road_tax_expiry",
    )

    list_filter = (
        "status",
        "bus_type",
    )

    search_fields = (
        "registration_number",
        "vehicle_name",
    )

    ordering = ("registration_number",)
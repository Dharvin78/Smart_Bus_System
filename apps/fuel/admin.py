# Register your models here.
from django.contrib import admin

from .models import Fuel


@admin.register(Fuel)
class FuelAdmin(admin.ModelAdmin):

    list_display = (
        "vehicle",
        "fuel_type",
        "refill_date",
        "litres",
        "price_per_litre",
        "total_cost",
        "fuel_station",
    )

    search_fields = (
        "vehicle__registration_number",
        "fuel_station",
        "fuel_type",
    )

    list_filter = (
        "fuel_type",
        "refill_date",
    )

    ordering = (
        "-refill_date",
    )
# Register your models here.
from django.contrib import admin

from .models import Maintenance


@admin.register(Maintenance)
class MaintenanceAdmin(admin.ModelAdmin):

    list_display = (
        "vehicle",
        "maintenance_type",
        "workshop",
        "service_date",
        "next_service_date",
        "cost",
        "status",
    )

    list_filter = (
        "maintenance_type",
        "status",
        "service_date",
    )

    search_fields = (
        "vehicle__registration_number",
        "vehicle__vehicle_name",
        "workshop",
        "maintenance_type",
    )

    ordering = (
        "-service_date",
    )
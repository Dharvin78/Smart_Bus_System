# Register your models here.
from django.contrib import admin
from .models import Driver


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):

    list_display = (
        "full_name",
        "phone",
        "driving_license",
        "assigned_vehicle",
        "status",
    )

    search_fields = (
        "full_name",
        "phone",
        "driving_license",
    )

    list_filter = (
        "status",
    )
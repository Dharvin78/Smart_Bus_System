# Register your models here.
from django.contrib import admin
from .models import Driver


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):

    list_display = (
        "full_name",
        "phone",
        "assigned_vehicle",
        "status",
    )

    search_fields = (
        "full_name",
        "phone",
    )

    list_filter = (
        "status",
    )
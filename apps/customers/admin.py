# Register your models here.
from django.contrib import admin
from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):

    list_display = (
        "first_name",
        "last_name",
        "email",
        "phone",
        "city",
        "gender",
    )

    search_fields = (
        "first_name",
        "last_name",
        "email",
        "phone",
    )

    list_filter = (
        "gender",
        "city",
    )
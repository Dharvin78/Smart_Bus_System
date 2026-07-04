# Register your models here.
from django.contrib import admin
from .models import CustomerProfile


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "phone",
        "city",
        "country",
    )

    search_fields = (
        "user__username",
        "phone",
        "city",
    )
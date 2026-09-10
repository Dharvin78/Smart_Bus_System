from django.urls import path
from . import views

app_name = "bookings"

urlpatterns = [

    path(
        "",
        views.booking_list,
        name="booking_list",
    ),

    path(
        "add/",
        views.booking_create,
        name="booking_create",
    ),

    path(
        "edit/<int:pk>/",
        views.booking_update,
        name="booking_update",
    ),

    path(
        "delete/<int:pk>/",
        views.booking_delete,
        name="booking_delete",
    ),

    path(
        "driver-trips/",
        views.driver_trips,
        name="driver_trips"
    ),

]
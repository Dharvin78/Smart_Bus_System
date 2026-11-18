from django.urls import path
from . import views
from . import review_views

app_name = "bookings"

urlpatterns = [

    path("", views.booking_list, name="booking_list",),

    path("add/", views.booking_create, name="booking_create",),

    path("driver-trips/", views.driver_trips, name="driver_trips"),

    path("my-bookings/", views.customer_bookings, name="customer_bookings"),

    path("<int:pk>/review/", review_views.booking_review, name="booking_review"),

    path("cancel/<int:pk>/", views.customer_cancel_booking, name="customer_cancel_booking",),

]

from django.urls import path
from . import views

app_name = "drivers"

urlpatterns = [

    # Customer Driver Reviews
    path(
        "review/<int:booking_id>/",
        views.driver_review,
        name="driver_review",
    ),

    # Driver Calendar
    path(
        "calendar/",
        views.driver_calendar,
        name="driver_calendar",
    ),

    # Driver Calendar Events
    path(
        "calendar/events/",
        views.driver_calendar_events,
        name="driver_calendar_events",
    ),

]

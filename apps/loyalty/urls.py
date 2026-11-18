from django.urls import path

from . import views

app_name = "loyalty"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("redeem/<int:booking_id>/", views.redeem, name="redeem"),
]

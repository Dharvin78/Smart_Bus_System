from django.urls import path
from . import views

urlpatterns = [
    path(
        "dashboard/",
        views.dashboard,
        name="dashboard",
    ),
    path(
        "customer/",
        views.customer_dashboard,
        name="customer_dashboard",
    ),
    path(
        "driver/",
        views.driver_dashboard,
        name="driver_dashboard",
    ),
]
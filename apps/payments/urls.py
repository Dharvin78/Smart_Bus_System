from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path(
        "",
        views.payment_list,
        name="payment_list",
    ),
    path(
        "add/",
        views.payment_create,
        name="payment_create",
    ),
    path(
        "receipt/<int:pk>/",
        views.payment_receipt,
        name="payment_receipt",
    ),
]
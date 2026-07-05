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
        "edit/<int:pk>/",
        views.payment_update,
        name="payment_update",
    ),

    path(
        "delete/<int:pk>/",
        views.payment_delete,
        name="payment_delete",
    ),

]
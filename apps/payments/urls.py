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

    path(
        "receipt/<int:pk>/",
        views.payment_receipt,
        name="payment_receipt",
    ),

    path("approve/<int:pk>/", views.payment_approve, name="payment_approve",),

    path("reject/<int:pk>/",views.payment_reject,name="payment_reject",),

]
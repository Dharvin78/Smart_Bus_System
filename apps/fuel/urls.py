from django.urls import path

from . import views

app_name = "fuel"

urlpatterns = [

    path(
        "",
        views.fuel_list,
        name="fuel_list",
    ),

    path(
        "add/",
        views.fuel_create,
        name="fuel_create",
    ),

    path(
        "edit/<int:pk>/",
        views.fuel_update,
        name="fuel_update",
    ),

    path(
        "delete/<int:pk>/",
        views.fuel_delete,
        name="fuel_delete",
    ),

]
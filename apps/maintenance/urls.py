from django.urls import path

from . import views

app_name = "maintenance"

urlpatterns = [

    path(
        "",
        views.maintenance_list,
        name="maintenance_list",
    ),

    path(
        "add/",
        views.maintenance_create,
        name="maintenance_create",
    ),

    path(
        "edit/<int:pk>/",
        views.maintenance_update,
        name="maintenance_update",
    ),

    path(
        "delete/<int:pk>/",
        views.maintenance_delete,
        name="maintenance_delete",
    ),

]
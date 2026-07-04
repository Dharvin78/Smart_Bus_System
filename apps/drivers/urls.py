from django.urls import path
from . import views

app_name = "drivers"

urlpatterns = [

    path("", views.driver_list, name="driver_list"),

    path("add/", views.driver_create, name="driver_create"),

    path("edit/<int:pk>/", views.driver_update, name="driver_update"),

    path("delete/<int:pk>/", views.driver_delete, name="driver_delete"),

]
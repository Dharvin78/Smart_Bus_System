from django.urls import path

from . import views

app_name = "ai_prediction"

urlpatterns = [

    path(
        "",
        views.prediction,
        name="prediction",
    ),

]
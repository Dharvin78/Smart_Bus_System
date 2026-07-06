# Create your views here.
from django.shortcuts import render

from .forms import PredictionForm
from .models import PredictionHistory
from .ml.predict import predict_cost


def prediction(request):

    predicted_cost = None

    if request.method == "POST":

        form = PredictionForm(request.POST)

        if form.is_valid():

            vehicle_type = form.cleaned_data["vehicle_type"]
            distance = form.cleaned_data["distance"]
            passengers = form.cleaned_data["passengers"]

            predicted_cost = predict_cost(
                vehicle_type,
                distance,
                passengers,
            )

            PredictionHistory.objects.create(
                vehicle_type=vehicle_type,
                distance=distance,
                passengers=passengers,
                predicted_cost=predicted_cost,
            )

    else:

        form = PredictionForm()

    return render(
        request,
        "ai_prediction/prediction.html",
        {
            "form": form,
            "predicted_cost": predicted_cost,
        },
    )
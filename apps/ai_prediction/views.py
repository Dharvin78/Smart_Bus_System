# Create your views here.
from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib import messages

from .forms import PredictionForm
from .models import PredictionHistory
from .ml.predict import predict_cost
from .ml.revenue_prediction import predict_revenue
from .ml.booking_prediction import predict_bookings
from .ml.maintenance_prediction import predict_maintenance
from .ml.maintenance_prediction_ml import train_maintenance_model

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

def prediction_dashboard(request):

    revenue_prediction = predict_revenue()
    booking_prediction = predict_bookings()
    maintenance_prediction = predict_maintenance()
    maintenance_ai = train_maintenance_model()

    forecast_labels = []
    forecast_data = []

    booking_labels = []
    booking_data = []

    if revenue_prediction:

        forecast_labels = revenue_prediction["labels"].copy()

        forecast_data = revenue_prediction["history"].copy()

        # Add next month label
        from datetime import datetime
        from dateutil.relativedelta import relativedelta

        last_month = datetime.strptime(
            forecast_labels[-1],
            "%b %Y"
        )

        next_month = (
            last_month + relativedelta(months=1)
        ).strftime("%b %Y")

        forecast_labels.append(next_month)

        forecast_data.append(
            revenue_prediction["prediction"]
        )

    if booking_prediction:

        booking_labels = booking_prediction["labels"].copy()

        booking_data = booking_prediction["history"].copy()

        from datetime import datetime
        from dateutil.relativedelta import relativedelta

        last = datetime.strptime(
            booking_labels[-1],
            "%b %Y"
        )

        next_month = (
            last + relativedelta(months=1)
        ).strftime("%b %Y")

        booking_labels.append(next_month)

        booking_data.append(
            booking_prediction["prediction"]
        )

    context = {

        "revenue_prediction": revenue_prediction,
        "forecast_labels": forecast_labels,
        "forecast_data": forecast_data,

        "booking_prediction": booking_prediction,
        "booking_forecast_labels": booking_labels,
        "booking_forecast_data": booking_data,
        "maintenance_prediction": maintenance_prediction,
        "maintenance_ai": maintenance_ai,

    }

    return render(
        request,
        "ai_prediction/prediction.html",
        context,
    )

def retrain_model(request):

    train_maintenance_model()

    messages.success(

        request,

        "AI model retrained successfully."

    )

    return redirect("ai_prediction:prediction")
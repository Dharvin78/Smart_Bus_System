import json

from django.shortcuts import render

from .insights import generate_ai_insights
from .report import generate_business_report

from .services import (
    train_revenue_model,
    get_revenue_history,
)


def ai_dashboard(request):

    train_revenue_model()

    history = get_revenue_history()

    prediction = (
        history["forecast"][-1]
        if history.get("forecast")
        and history["forecast"][-1] is not None
        else None
    )

    insights = generate_ai_insights(prediction)

    report = generate_business_report()

    context = {

        "labels": json.dumps(history["labels"]),

        "actual": json.dumps(history["actual"]),

        "forecast": json.dumps(history["forecast"]),

        "prediction": prediction,

        "insights": insights,

        "report": report,

    }

    return render(
        request,
        "ai/dashboard.html",
        context,
    )
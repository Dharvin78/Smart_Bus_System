import pandas as pd

from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    r2_score,
    mean_absolute_error,
    mean_squared_error,
)

from django.db.models import Sum
from django.db.models.functions import TruncMonth

from apps.payments.models import Payment


def predict_revenue():

    revenue = (
        Payment.objects
        .filter(payment_status="Paid")
        .annotate(month=TruncMonth("payment_date"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )

    if revenue.count() < 2:
        return None

    months = []
    totals = []
    month_labels = []

    index = 1

    for row in revenue:
        month_labels.append(row["month"].strftime("%b %Y"))

    df = pd.DataFrame({

        "month": months,

        "revenue": totals,

    })

    X = df[["month"]]
    y = df["revenue"]

    model = LinearRegression()

    model.fit(X, y)

    next_month = pd.DataFrame({
        "month": [len(df) + 1]
    })

    prediction = model.predict(next_month)[0]

    predicted_existing = model.predict(X)

    return {

        "prediction": round(prediction, 2),

        "r2": round(r2_score(y, predicted_existing), 3),

        "mae": round(
            mean_absolute_error(y, predicted_existing),
            2
        ),

        "rmse": round(
            mean_squared_error(
                y,
                predicted_existing
            ) ** 0.5,
            2
        ),

        "labels": month_labels,

        "history": totals,

    }
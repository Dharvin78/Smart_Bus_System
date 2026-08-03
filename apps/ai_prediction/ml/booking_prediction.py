import pandas as pd

from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    r2_score,
    mean_absolute_error,
    mean_squared_error,
)

from django.db.models import Count
from django.db.models.functions import TruncMonth

from apps.bookings.models import Booking


def predict_bookings():

    bookings = (
        Booking.objects
        .annotate(month=TruncMonth("travel_date"))
        .values("month")
        .annotate(total=Count("id"))
        .order_by("month")
    )

    if bookings.count() < 2:
        return None

    labels = []
    totals = []

    month_number = []

    i = 1

    for row in bookings:

        labels.append(row["month"].strftime("%b %Y"))
        totals.append(row["total"])
        month_number.append(i)

        i += 1

    df = pd.DataFrame({

        "month": month_number,

        "bookings": totals

    })

    X = df[["month"]]
    y = df["bookings"]

    model = LinearRegression()

    model.fit(X, y)

    next_month = pd.DataFrame({

        "month": [len(df) + 1]

    })

    prediction = model.predict(next_month)[0]

    predicted = model.predict(X)

    return {

        "prediction": round(prediction),

        "labels": labels,

        "history": totals,

        "r2": round(
            r2_score(y, predicted),
            3
        ),

        "mae": round(
            mean_absolute_error(y, predicted),
            2
        ),

        "rmse": round(
            mean_squared_error(
                y,
                predicted
            ) ** 0.5,
            2
        )

    }
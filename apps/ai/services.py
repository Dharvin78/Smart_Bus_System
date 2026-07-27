import os
import joblib
import pandas as pd

from django.db.models import Sum
from django.db.models.functions import ExtractMonth
from sklearn.linear_model import LinearRegression

from apps.payments.models import Payment
from .predictor import predict_next_month_revenue
from collections import OrderedDict

MODEL_PATH = "ml_models/revenue_model.pkl"

def get_revenue_history():

    payments = (
        Payment.objects
        .filter(payment_status="Paid")
        .order_by("payment_date")
    )

    monthly = OrderedDict()

    for payment in payments:

        month = payment.payment_date.strftime("%b %Y")

        monthly.setdefault(month, 0)

        monthly[month] += float(payment.amount)

    labels = list(monthly.keys())
    actual = list(monthly.values())

    prediction = predict_next_month()

    forecast = [None] * len(actual)

    if prediction is not None:

        forecast[-1] = actual[-1]

        labels.append("Next Month")

        actual.append(None)

        forecast.append(prediction)

    return {
        "labels": labels,
        "actual": actual,
        "forecast": forecast,
    }

def train_revenue_model():

    payments = Payment.objects.filter(
        payment_status="Paid"
    ).order_by("payment_date")

    if payments.count() < 10:
        return None

    df = pd.DataFrame(
        list(
            payments.values(
                "payment_date",
                "amount"
            )
        )
    )

    df["payment_date"] = pd.to_datetime(df["payment_date"])

    monthly = (
        df.groupby(
            df["payment_date"].dt.to_period("M")
        )["amount"]
        .sum()
        .reset_index()
    )

    monthly["month"] = range(1, len(monthly)+1)

    X = monthly[["month"]]

    y = monthly["amount"]

    model = LinearRegression()

    model.fit(X, y)

    os.makedirs("ml_models", exist_ok=True)

    joblib.dump(model, MODEL_PATH)

    return model

def predict_next_month():

    if not os.path.exists(MODEL_PATH):
        return None

    model = joblib.load(MODEL_PATH)

    payments = Payment.objects.filter(
        payment_status="Paid"
    )

    df = pd.DataFrame(
        list(
            payments.values(
                "payment_date",
                "amount"
            )
        )
    )

    df["payment_date"] = pd.to_datetime(df["payment_date"])

    monthly = (
        df.groupby(
            df["payment_date"].dt.to_period("M")
        )["amount"]
        .sum()
        .reset_index()
    )

    next_month = len(monthly) + 1

    prediction = model.predict([[next_month]])[0]

    return round(prediction, 2)
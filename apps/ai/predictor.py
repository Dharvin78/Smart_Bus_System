import pandas as pd
from sklearn.linear_model import LinearRegression


def predict_next_month_revenue(payments):

    if len(payments) < 2:
        return None

    df = pd.DataFrame(payments)

    X = df[["month"]]
    y = df["revenue"]

    model = LinearRegression()
    model.fit(X, y)

    next_month = [[df["month"].max() + 1]]

    prediction = model.predict(next_month)

    return round(float(prediction[0]), 2)
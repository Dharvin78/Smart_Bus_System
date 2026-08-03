import os
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
)

from apps.maintenance.models import Maintenance


def train_maintenance_model():

    records = Maintenance.objects.all()

    if records.count() < 10:
        return None

    data = []

    for row in records:

        data.append({

            "mileage": row.mileage,

            "cost": float(row.cost),

            "maintenance_type": row.maintenance_type,

            "status": row.status,

            "label": row.needs_maintenance,

        })

    df = pd.DataFrame(data)

    type_encoder = LabelEncoder()
    status_encoder = LabelEncoder()
    label_encoder = LabelEncoder()

    df["maintenance_type"] = type_encoder.fit_transform(
        df["maintenance_type"]
    )

    df["status"] = status_encoder.fit_transform(
        df["status"]
    )

    df["label"] = label_encoder.fit_transform(
        df["label"]
    )

    X = df[
        [
            "mileage",
            "cost",
            "maintenance_type",
            "status",
        ]
    ]

    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(

        X,
        y,

        test_size=0.2,

        random_state=42,

        stratify=y

    )

    model = RandomForestClassifier(

        n_estimators=100,

        random_state=42

    )

    model.fit(

        X_train,

        y_train

    )

    prediction = model.predict(X_test)

    accuracy = accuracy_score(

        y_test,

        prediction

    )

    precision = precision_score(

        y_test,

        prediction,

        zero_division=0

    )

    recall = recall_score(

        y_test,

        prediction,

        zero_division=0

    )

    f1 = f1_score(

        y_test,

        prediction,

        zero_division=0

    )

    feature_importance = []

    for name, value in zip(

        X.columns,

        model.feature_importances_

    ):

        feature_importance.append({

            "feature": name,

            "importance": round(value * 100, 2)

        })

    feature_importance.sort(

        key=lambda x: x["importance"],

        reverse=True

    )

    # Save the trained model and encoders
    MODEL_PATH = os.path.join(
        os.path.dirname(__file__),
        "..",
        "models",
        "maintenance_model.pkl",
    )

    model.fit(
        X_train,
        y_train
    )

    os.makedirs(
        os.path.dirname(MODEL_PATH),
        exist_ok=True,
    )

    joblib.dump(
        model,
        MODEL_PATH,
    )

    return {

        "accuracy": round(accuracy * 100, 2),

        "precision": round(precision * 100, 2),

        "recall": round(recall * 100, 2),

        "f1": round(f1 * 100, 2),

        "importance": feature_importance,

    }

def load_model():

    if os.path.exists(MODEL_PATH):

        return joblib.load(MODEL_PATH)

    return None

def predict_vehicle(

    mileage,

    cost,

    maintenance_type,

    status,

):

    model = load_model()

    if model is None:

        return None

    # Encode values exactly the same
    # as during training

    type_map = {

        "Oil Change":0,
        "Engine Service":1,
        "Brake Service":2,
        "Tyre Replacement":3,
        "Air Conditioning":4,
        "Battery Replacement":5,
        "General Inspection":6,
        "Other":7,

    }

    status_map = {

        "Scheduled":0,
        "In Progress":1,
        "Completed":2,
        "Cancelled":3,

    }

    prediction = model.predict([[
        mileage,
        cost,
        type_map[maintenance_type],
        status_map[status],
    ]])

    probability = model.predict_proba([[
        mileage,
        cost,
        type_map[maintenance_type],
        status_map[status],
    ]])

    confidence = max(probability[0]) * 100

    return {

        "prediction": "Yes" if prediction[0] else "No",

        "confidence": round(confidence,2)

    }
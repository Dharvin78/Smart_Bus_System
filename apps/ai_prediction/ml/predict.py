import os
import joblib
import pandas as pd

BASE_DIR = os.path.dirname(__file__)

MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")
ENCODER_PATH = os.path.join(BASE_DIR, "encoder.pkl")

model = None
encoder = None

if (
    os.path.exists(MODEL_PATH)
    and os.path.getsize(MODEL_PATH) > 0
    and os.path.exists(ENCODER_PATH)
    and os.path.getsize(ENCODER_PATH) > 0
):
    model = joblib.load(MODEL_PATH)
    encoder = joblib.load(ENCODER_PATH)


def predict_cost(vehicle_type, distance, passengers):

    if model is None or encoder is None:
        raise Exception(
            "AI model has not been trained yet. Please train the model first."
        )

    vehicle = encoder.transform([vehicle_type])[0]

    X = pd.DataFrame(
        {
            "vehicle_type": [vehicle],
            "distance": [distance],
            "passengers": [passengers],
        }
    )

    prediction = model.predict(X)

    return round(float(prediction[0]), 2)
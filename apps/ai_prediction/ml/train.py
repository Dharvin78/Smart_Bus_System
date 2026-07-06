import os
import django
from apps.vehicles.models import Vehicle

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)

django.setup()

import joblib
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder

from apps.bookings.models import Booking


bookings = Booking.objects.all()

if bookings.count() == 0:
    print("No booking data found.")
    exit()


data = []

for booking in bookings:

    data.append({

        "vehicle_type": booking.vehicle.bus_type,

        "distance": 0,   # Temporary

        "passengers": booking.passenger_count,

        "price": float(booking.total_price),

    })


df = pd.DataFrame(data)


all_bus_types = list(
    Vehicle.objects.values_list("bus_type", flat=True).distinct()
)

encoder = LabelEncoder()
encoder.fit(all_bus_types)

df["vehicle_type"] = encoder.transform(df["vehicle_type"])


X = df[
    [
        "vehicle_type",
        "distance",
        "passengers",
    ]
]

y = df["price"]


model = RandomForestRegressor(
    n_estimators=100,
    random_state=42,
)

model.fit(X, y)


BASE = os.path.dirname(__file__)

joblib.dump(
    model,
    os.path.join(BASE, "model.pkl"),
)

joblib.dump(
    encoder,
    os.path.join(BASE, "encoder.pkl"),
)

print("Model trained successfully.")
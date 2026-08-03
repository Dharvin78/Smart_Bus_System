from django.utils import timezone
from datetime import timedelta

from apps.maintenance.models import Maintenance


def predict_maintenance():

    upcoming = []

    records = Maintenance.objects.select_related("vehicle")

    for record in records:

        if record.next_service_date:

            days = (
                record.next_service_date - timezone.now().date()
            ).days

            if days <= 30:

                if days <= 7:
                    risk = "High"

                elif days <= 14:
                    risk = "Medium"

                else:
                    risk = "Low"

                upcoming.append({

                    "vehicle": record.vehicle.vehicle_name,

                    "service_date": record.next_service_date,

                    "days": days,

                    "risk": risk

                })

    upcoming.sort(key=lambda x: x["days"])

    return upcoming
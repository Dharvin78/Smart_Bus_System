# Create your models here.
from django.db import models


class PredictionHistory(models.Model):

    vehicle_type = models.CharField(max_length=50)

    distance = models.FloatField()

    passengers = models.PositiveIntegerField()

    predicted_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    prediction_date = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-prediction_date"]

    def __str__(self):
        return f"{self.vehicle_type} - RM {self.predicted_cost}"
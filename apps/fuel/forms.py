
from django import forms

from .models import Fuel


class FuelForm(forms.ModelForm):

    class Meta:
        model = Fuel

        fields = [
            "vehicle",
            "fuel_type",
            "refill_date",
            "litres",
            "price_per_litre",
            "fuel_station",
            "mileage",
            "remarks",
        ]

        widgets = {
            "vehicle": forms.Select(attrs={
                "class": "form-select"
            }),

            "fuel_type": forms.Select(attrs={
                "class": "form-select"
            }),

            "refill_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),

            "litres": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0.01",
                "placeholder": "Fuel Litres"
            }),

            "price_per_litre": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0.01",
                "placeholder": "Price Per Litre"
            }),

            "fuel_station": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Fuel Station"
            }),

            "mileage": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
                "placeholder": "Mileage (km)"
            }),

            "remarks": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Remarks"
            }),
        }

    # ==========================================
    # VALIDATE FUEL LITRES
    # ==========================================
    def clean_litres(self):

        litres = self.cleaned_data.get("litres")

        if litres is not None and litres <= 0:
            raise forms.ValidationError(
                "Fuel litres must be greater than zero."
            )

        return litres

    # ==========================================
    # VALIDATE PRICE PER LITRE
    # ==========================================
    def clean_price_per_litre(self):

        price = self.cleaned_data.get("price_per_litre")

        if price is not None and price <= 0:
            raise forms.ValidationError(
                "Price per litre must be greater than zero."
            )

        return price

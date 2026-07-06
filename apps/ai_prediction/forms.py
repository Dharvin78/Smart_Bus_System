from django import forms


class PredictionForm(forms.Form):

    VEHICLE_CHOICES = [

        ("Mini Bus", "Mini Bus"),

        ("Standard Bus", "Standard Bus"),

        ("VIP Coach", "VIP Coach"),

    ]

    vehicle_type = forms.ChoiceField(

        choices=VEHICLE_CHOICES,

        widget=forms.Select(attrs={
            "class": "form-select"
        })

    )

    distance = forms.FloatField(

        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "placeholder": "Distance (KM)"
        })

    )

    passengers = forms.IntegerField(

        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "placeholder": "Passengers"
        })

    )
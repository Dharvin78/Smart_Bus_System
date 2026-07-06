from django import forms

from .models import Maintenance


class MaintenanceForm(forms.ModelForm):

    class Meta:

        model = Maintenance

        fields = [
            "vehicle",
            "maintenance_type",
            "workshop",
            "service_date",
            "next_service_date",
            "mileage",
            "cost",
            "status",
            "remarks",
        ]

        widgets = {

            "vehicle": forms.Select(attrs={
                "class": "form-select"
            }),

            "maintenance_type": forms.Select(attrs={
                "class": "form-select"
            }),

            "workshop": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Workshop Name"
            }),

            "service_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),

            "next_service_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),

            "mileage": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Mileage (km)"
            }),

            "cost": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Maintenance Cost"
            }),

            "status": forms.Select(attrs={
                "class": "form-select"
            }),

            "remarks": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Remarks (Optional)"
            }),

        }

    def clean(self):

        cleaned_data = super().clean()

        service_date = cleaned_data.get("service_date")
        next_service_date = cleaned_data.get("next_service_date")

        if (
            service_date and
            next_service_date and
            next_service_date < service_date
        ):
            self.add_error(
                "next_service_date",
                "Next service date cannot be earlier than the service date."
            )

        return cleaned_data
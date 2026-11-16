from django import forms

from .models import Maintenance
from django.db.models import Q
from apps.drivers.models import Driver
from apps.bookings.models import Booking

class MaintenanceForm(forms.ModelForm):

    class Meta:

        model = Maintenance

        fields = [
            "vehicle",
            "assigned_driver",
            "maintenance_type",
            "workshop",
            "service_date",
            "start_time",
            "next_service_date",
            "mileage",
            "cost",
            "status",
            "needs_maintenance",
            "remarks",
        ]

        widgets = {

            "vehicle": forms.Select(attrs={
                "class": "form-select"
            }),

            "assigned_driver": forms.Select(attrs={
                "class": "form-select",
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

            "needs_maintenance": forms.Select(attrs={
                "class": "form-select"
            }),

            "start_time": forms.TimeInput(
                format="%H:%M",
                attrs={
                    "class": "form-control",
                    "type": "time",
                }
            ),

        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["assigned_driver"].queryset = (
            Driver.objects.filter(
                status__in=["Available", "Reserved", "On Trip"]
            ).order_by("full_name")
        )

        self.fields["assigned_driver"].empty_label = (
            "-- Select Driver (Optional) --"
        )

        # Preserve the current assigned driver when editing.
        if self.instance.pk and self.instance.assigned_driver_id:
            self.fields["assigned_driver"].queryset = (
                Driver.objects.filter(
                    Q(status__in=["Available", "Reserved", "On Trip"]) |
                    Q(pk=self.instance.assigned_driver_id)
                ).distinct().order_by("full_name")
            )
    
    
    def clean(self):
        cleaned_data = super().clean()

        vehicle = cleaned_data.get("vehicle")
        assigned_driver = cleaned_data.get("assigned_driver")
        service_date = cleaned_data.get("service_date")
        next_service_date = cleaned_data.get("next_service_date")
        status = cleaned_data.get("status")

        # Validate next service date.
        if (
            service_date
            and next_service_date
            and next_service_date < service_date
        ):
            self.add_error(
                "next_service_date",
                "Next service date cannot be earlier than the service date."
            )

        # Completed and Cancelled maintenance does not
        # reserve the vehicle or driver.
        if status in ("Completed", "Cancelled"):
            return cleaned_data

        if not service_date:
            return cleaned_data

        # Check confirmed bookings covering the service date.
        confirmed_bookings = Booking.objects.filter(
            booking_status="Confirmed",
            travel_date__lte=service_date,
        ).filter(
            Q(return_date__gte=service_date) |
            Q(
                return_date__isnull=True,
                travel_date=service_date,
            )
        )

        # Check vehicle booking conflicts.
        if vehicle is not None:
            if confirmed_bookings.filter(vehicle=vehicle).exists():
                self.add_error(
                    "vehicle",
                    "This vehicle has a confirmed booking "
                    "on the selected maintenance date."
                )

        # Check driver booking conflicts.
        if assigned_driver is not None:
            if confirmed_bookings.filter(
                driver=assigned_driver
            ).exists():
                self.add_error(
                    "assigned_driver",
                    "This driver has a confirmed booking "
                    "on the selected maintenance date."
                )

        # Check other maintenance records on the same date.
        existing_maintenance = Maintenance.objects.filter(
            service_date=service_date,
            status__in=["Scheduled", "In Progress"],
        )

        # Exclude the current record when editing.
        if self.instance.pk:
            existing_maintenance = existing_maintenance.exclude(
                pk=self.instance.pk
            )

        # Prevent overlapping vehicle maintenance.
        if vehicle is not None:
            if existing_maintenance.filter(vehicle=vehicle).exists():
                self.add_error(
                    "vehicle",
                    "This vehicle already has a maintenance "
                    "assignment on the selected service date."
                )

        # Prevent overlapping driver maintenance.
        if assigned_driver is not None:
            if existing_maintenance.filter(
                assigned_driver=assigned_driver
            ).exists():
                self.add_error(
                    "assigned_driver",
                    "This driver already has a maintenance "
                    "assignment on the selected service date."
                )


        return cleaned_data


    def clean_cost(self):
        cost = self.cleaned_data["cost"]

        if cost < 0:
            raise forms.ValidationError(
                "Maintenance cost cannot be negative."
            )

        return cost
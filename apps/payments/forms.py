from django import forms

from .models import Payment


class PaymentForm(forms.ModelForm):

    class Meta:

        model = Payment

        fields = [
            "booking",
            "amount",
            "payment_method",
            "payment_status",
            "transaction_id",
            "payment_date",
            "remarks",
        ]

        widgets = {

            "booking": forms.Select(attrs={
                "class": "form-select"
            }),

            "amount": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "placeholder": "Payment Amount"
            }),

            "payment_method": forms.Select(attrs={
                "class": "form-select"
            }),

            "payment_status": forms.Select(attrs={
                "class": "form-select"
            }),

            "transaction_id": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Transaction / Receipt Number"
            }),

            "payment_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),

            "remarks": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Remarks (Optional)"
            }),

        }
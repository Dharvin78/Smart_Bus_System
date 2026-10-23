from django import forms
from .models import Payment


class CustomerPaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["payment_method"]

        widgets = {
            "payment_method": forms.Select(attrs={
                "class": "checkout-input",
            }),
        }

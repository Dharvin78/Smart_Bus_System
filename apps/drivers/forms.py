
from django import forms
from .models import DriverReview


class DriverReviewForm(forms.ModelForm):

    class Meta:
        model = DriverReview

        fields = [
            "rating",
            "comment",
        ]

        widgets = {
            "rating": forms.RadioSelect(
                choices=[
                    (1, "1"),
                    (2, "2"),
                    (3, "3"),
                    (4, "4"),
                    (5, "5"),
                ],
                attrs={
                    "class": "rating-input"
                }
            ),

            "comment": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Tell us about your experience with the driver..."
            }),
        }

        labels = {
            "rating": "Driver Rating",
            "comment": "Comment",
        }

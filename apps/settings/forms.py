from django import forms

from .models import SystemSetting


class SystemSettingForm(forms.ModelForm):

    class Meta:

        model = SystemSetting

        fields = "__all__"

        widgets = {

            "company_address": forms.Textarea(
                attrs={"rows":3}
            )

        }
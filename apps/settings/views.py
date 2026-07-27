from django.shortcuts import render

from .models import SystemSetting
from .forms import SystemSettingForm
from django.contrib import messages


def settings_page(request):

    setting, created = SystemSetting.objects.get_or_create(pk=1)

    if request.method == "POST":

        form = SystemSettingForm(
            request.POST,
            request.FILES,
            instance=setting
        )

        if form.is_valid():

            form.save()
            
            messages.success(
                request,
                "System settings updated successfully."
            )

    else:

        form = SystemSettingForm(instance=setting)

    return render(
        request,
        "settings/settings.html",
        {
            "form": form
        }
    )
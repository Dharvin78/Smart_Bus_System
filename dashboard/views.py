# Create your views here.
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):

    context = {
        "total_revenue": 0,
        "total_bookings": 0,
        "total_vehicles": 0,
        "maintenance_due": 0,
    }

    return render(
        request,
        "dashboard/dashboard.html",
        context
    )
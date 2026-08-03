from django.shortcuts import render
from django.db.models import Sum
from django.db.models.functions import TruncMonth

from apps.payments.models import Payment


def dashboard(request):

    monthly_revenue = (
        Payment.objects
        .filter(payment_status="Paid")
        .annotate(month=TruncMonth("payment_date"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )

    labels = []
    revenue = []

    for item in monthly_revenue:
        labels.append(item["month"].strftime("%b %Y"))
        revenue.append(float(item["total"]))

    context = {
        "labels": labels,
        "revenue": revenue,
    }

    return render(
        request,
        "analytics/dashboard.html",
        context,
    )
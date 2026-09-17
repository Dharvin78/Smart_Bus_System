# Create your views here.

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponse

from .pdf_utils import build_maintenance_pdf
from .pdf_utils import build_fuel_pdf
from apps.accounts.models import UserProfile
from django.db.models import Sum, Avg, Count
from apps.fuel.models import Fuel
from apps.maintenance.models import Maintenance
from apps.vehicles.models import Vehicle
from apps.payments.models import Payment
from .pdf_utils import build_revenue_pdf

@login_required
def report_dashboard(request):

    current_role = request.user.profile.role

    # Only Owner and Admin can access reports
    if current_role not in [
        UserProfile.OWNER,
        UserProfile.ADMIN,
    ]:
        messages.error(
            request,
            "You do not have permission to access reports."
        )

        return redirect("dashboard")

    return render(
        request,
        "reports/dashboard.html",
        {
            "role": current_role,
        }
    )

# FUEL USAGE REPORT
@login_required
def fuel_report(request):

    current_role = request.user.profile.role

    # Only Owner and Admin can access reports
    if current_role not in [
        UserProfile.OWNER,
        UserProfile.ADMIN,
    ]:
        messages.error(
            request,
            "You do not have permission to access reports."
        )
        return redirect("dashboard")

    # Get fuel records
    fuels = Fuel.objects.select_related(
        "vehicle"
    ).all().order_by("-refill_date")

    # Filters
    vehicle_id = request.GET.get("vehicle", "").strip()
    start_date = request.GET.get("start_date", "").strip()
    end_date = request.GET.get("end_date", "").strip()

    # Vehicle filter
    if vehicle_id:
        fuels = fuels.filter(
            vehicle_id=vehicle_id
        )

    # Start date filter
    if start_date:
        fuels = fuels.filter(
            refill_date__gte=start_date
        )

    # End date filter
    if end_date:
        fuels = fuels.filter(
            refill_date__lte=end_date
        )

    # ---------------------------------
    # Summary
    # ---------------------------------

    summary = fuels.aggregate(
        total_litres=Sum("litres"),
        total_cost=Sum("total_cost"),
        average_price=Avg("price_per_litre"),
        total_refills=Count("id"),
    )

    # ---------------------------------
    # Vehicles for filter dropdown
    # ---------------------------------

    vehicles = Vehicle.objects.all().order_by(
        "registration_number"
    )

    # ---------------------------------
    # Context
    # ---------------------------------

    context = {
        "fuels": fuels,
        "summary": summary,
        "vehicles": vehicles,

        "selected_vehicle": vehicle_id,
        "start_date": start_date,
        "end_date": end_date,

        "role": current_role,
    }

    return render(
        request,
        "reports/fuel_report.html",
        context
    )


# =========================================================
# FUEL USAGE PDF REPORT
# =========================================================

@login_required
def fuel_report_pdf(request):

    current_role = request.user.profile.role

    if current_role not in [
        UserProfile.OWNER,
        UserProfile.ADMIN,
    ]:
        messages.error(
            request,
            "You do not have permission to generate reports."
        )
        return redirect("dashboard")

    fuels = Fuel.objects.select_related(
        "vehicle"
    ).all().order_by("-refill_date")

    vehicle_id = request.GET.get("vehicle", "").strip()
    start_date = request.GET.get("start_date", "").strip()
    end_date = request.GET.get("end_date", "").strip()

    # ---------------------------------
    # Filters
    # ---------------------------------

    if vehicle_id:
        fuels = fuels.filter(
            vehicle_id=vehicle_id
        )

    if start_date:
        fuels = fuels.filter(
            refill_date__gte=start_date
        )

    if end_date:
        fuels = fuels.filter(
            refill_date__lte=end_date
        )

    # ---------------------------------
    # Summary
    # ---------------------------------

    summary = fuels.aggregate(
        total_litres=Sum("litres"),
        total_cost=Sum("total_cost"),
        average_price=Avg("price_per_litre"),
        total_refills=Count("id"),
    )

    # ---------------------------------
    # Generate PDF
    # ---------------------------------

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'attachment; filename="fuel_usage_report.pdf"'
    )

    build_fuel_pdf(
        response,
        fuels,
        summary,
        start_date=start_date,
        end_date=end_date,
        selected_vehicle=vehicle_id,
    )

    return response

#Maintenance Modules
@login_required
def maintenance_report(request):

    # ---------------------------------
    # Permission
    # ---------------------------------

    current_role = request.user.profile.role

    if current_role not in [
        UserProfile.OWNER,
        UserProfile.ADMIN,
    ]:
        return render(
            request,
            "403.html",
            status=403
        )

    # ---------------------------------
    # Filters
    # ---------------------------------

    start_date = request.GET.get("start_date", "").strip()
    end_date = request.GET.get("end_date", "").strip()
    vehicle_id = request.GET.get("vehicle", "").strip()
    maintenance_type = request.GET.get(
        "maintenance_type",
        ""
    ).strip()

    records = Maintenance.objects.select_related(
        "vehicle"
    ).all()

    # ---------------------------------
    # Date filter
    # ---------------------------------

    if start_date:
        records = records.filter(
            service_date__gte=start_date
        )

    if end_date:
        records = records.filter(
            service_date__lte=end_date
        )

    # ---------------------------------
    # Vehicle filter
    # ---------------------------------

    if vehicle_id:
        records = records.filter(
            vehicle_id=vehicle_id
        )

    # ---------------------------------
    # Maintenance type filter
    # ---------------------------------

    if maintenance_type:
        records = records.filter(
            maintenance_type=maintenance_type
        )

    # ---------------------------------
    # Summary
    # ---------------------------------

    total_records = records.count()

    total_cost = (
        records.aggregate(
            total=Sum("cost")
        )["total"]
        or 0
    )

    completed_count = records.filter(
        status="Completed"
    ).count()

    scheduled_count = records.filter(
        status="Scheduled"
    ).count()

    in_progress_count = records.filter(
        status="In Progress"
    ).count()

    cancelled_count = records.filter(
        status="Cancelled"
    ).count()

    # ---------------------------------
    # Data for filters
    # ---------------------------------

    vehicles = Vehicle.objects.all().order_by(
        "registration_number"
    )

    maintenance_types = [
        choice[0]
        for choice in Maintenance.MAINTENANCE_TYPE_CHOICES
    ]

    # ---------------------------------
    # Context
    # ---------------------------------

    context = {
        "records": records,

        "total_records": total_records,
        "total_cost": total_cost,

        "completed_count": completed_count,
        "scheduled_count": scheduled_count,
        "in_progress_count": in_progress_count,
        "cancelled_count": cancelled_count,

        "vehicles": vehicles,
        "maintenance_types": maintenance_types,

        "start_date": start_date,
        "end_date": end_date,
        "selected_vehicle": vehicle_id,
        "selected_type": maintenance_type,

        "role": current_role,
    }

    return render(
        request,
        "reports/maintenance_report.html",
        context
    )

@login_required
def maintenance_report_pdf(request):

    current_role = request.user.profile.role

    if current_role not in [
        UserProfile.OWNER,
        UserProfile.ADMIN,
    ]:
        messages.error(
            request,
            "You do not have permission to generate reports."
        )
        return redirect("dashboard")

    records = Maintenance.objects.select_related(
        "vehicle"
    ).all()

    start_date = request.GET.get(
        "start_date",
        ""
    ).strip()

    end_date = request.GET.get(
        "end_date",
        ""
    ).strip()

    vehicle_id = request.GET.get(
        "vehicle",
        ""
    ).strip()

    maintenance_type = request.GET.get(
        "maintenance_type",
        ""
    ).strip()

    # ---------------------------------
    # Apply filters
    # ---------------------------------

    if start_date:
        records = records.filter(
            service_date__gte=start_date
        )

    if end_date:
        records = records.filter(
            service_date__lte=end_date
        )

    if vehicle_id:
        records = records.filter(
            vehicle_id=vehicle_id
        )

    if maintenance_type:
        records = records.filter(
            maintenance_type=maintenance_type
        )

    # ---------------------------------
    # Summary
    # ---------------------------------

    total_records = records.count()

    total_cost = (
        records.aggregate(
            total=Sum("cost")
        )["total"]
        or 0
    )

    completed_count = records.filter(
        status="Completed"
    ).count()

    scheduled_count = records.filter(
        status="Scheduled"
    ).count()

    in_progress_count = records.filter(
        status="In Progress"
    ).count()

    cancelled_count = records.filter(
        status="Cancelled"
    ).count()

    # ---------------------------------
    # PDF response
    # ---------------------------------

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'attachment; filename="maintenance_report.pdf"'
    )

    build_maintenance_pdf(
        response,
        records,
        total_records,
        total_cost,
        completed_count,
        scheduled_count,
        in_progress_count,
        cancelled_count,
        start_date=start_date,
        end_date=end_date,
        selected_vehicle=vehicle_id,
        selected_type=maintenance_type,
    )

    return response


# Revenue Report
@login_required
def revenue_report(request):

    current_role = request.user.profile.role

    # ---------------------------------
    # Permission
    # ---------------------------------

    if current_role not in [
        UserProfile.OWNER,
        UserProfile.ADMIN,
    ]:
        messages.error(
            request,
            "You do not have permission to access reports."
        )
        return redirect("dashboard")

    # ---------------------------------
    # Get paid payments
    # ---------------------------------

    payments = Payment.objects.select_related(
        "booking",
        "booking__customer",
    ).filter(
        payment_status="Paid"
    ).order_by("-payment_date")

    # ---------------------------------
    # Filters
    # ---------------------------------

    start_date = request.GET.get(
        "start_date",
        ""
    ).strip()

    end_date = request.GET.get(
        "end_date",
        ""
    ).strip()

    payment_method = request.GET.get(
        "payment_method",
        ""
    ).strip()

    # ---------------------------------
    # Date filter
    # ---------------------------------

    if start_date:
        payments = payments.filter(
            payment_date__gte=start_date
        )

    if end_date:
        payments = payments.filter(
            payment_date__lte=end_date
        )

    # ---------------------------------
    # Payment method filter
    # ---------------------------------

    if payment_method:
        payments = payments.filter(
            payment_method=payment_method
        )

    # ---------------------------------
    # Summary
    # ---------------------------------

    total_revenue = (
        payments.aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )

    total_transactions = payments.count()

    average_payment = (
        payments.aggregate(
            average=Avg("amount")
        )["average"]
        or 0
    )

    # ---------------------------------
    # Payment methods
    # ---------------------------------

    payment_methods = [
        choice[0]
        for choice in Payment.PAYMENT_METHOD_CHOICES
    ]

    # ---------------------------------
    # Context
    # ---------------------------------

    context = {

        "payments": payments,

        "total_revenue": total_revenue,
        "total_transactions": total_transactions,
        "average_payment": average_payment,

        "payment_methods": payment_methods,

        "start_date": start_date,
        "end_date": end_date,
        "selected_payment_method": payment_method,

        "role": current_role,
    }

    return render(
        request,
        "reports/revenue_report.html",
        context
    )

@login_required
def revenue_report_pdf(request):

    current_role = request.user.profile.role

    if current_role not in [
        UserProfile.OWNER,
        UserProfile.ADMIN,
    ]:
        messages.error(
            request,
            "You do not have permission to generate reports."
        )
        return redirect("dashboard")

    payments = Payment.objects.select_related(
        "booking",
        "booking__customer",
    ).all()

    # ---------------------------------
    # Filters
    # ---------------------------------

    start_date = request.GET.get(
        "start_date",
        ""
    ).strip()

    end_date = request.GET.get(
        "end_date",
        ""
    ).strip()

    payment_status = request.GET.get(
        "payment_status",
        ""
    ).strip()

    # ---------------------------------
    # Apply filters
    # ---------------------------------

    if start_date:
        payments = payments.filter(
            payment_date__gte=start_date
        )

    if end_date:
        payments = payments.filter(
            payment_date__lte=end_date
        )

    if payment_status:
        payments = payments.filter(
            payment_status=payment_status
        )

    # ---------------------------------
    # Summary
    # ---------------------------------

    total_revenue = (
        payments.filter(
            payment_status="Paid"
        ).aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )

    total_payments = payments.count()

    paid_count = payments.filter(
        payment_status="Paid"
    ).count()

    pending_count = payments.filter(
        payment_status="Pending"
    ).count()

    partially_paid_count = payments.filter(
        payment_status="Partially Paid"
    ).count()

    refunded_count = payments.filter(
        payment_status="Refunded"
    ).count()

    cancelled_count = payments.filter(
        payment_status="Cancelled"
    ).count()

    # ---------------------------------
    # PDF response
    # ---------------------------------

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'attachment; filename="revenue_report.pdf"'
    )

    build_revenue_pdf(
        response,
        payments,
        total_revenue,
        total_payments,
        paid_count,
        pending_count,
        partially_paid_count,
        refunded_count,
        cancelled_count,
        start_date=start_date,
        end_date=end_date,
        payment_status=payment_status,
    )

    return response
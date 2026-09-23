from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("", views.report_dashboard, name="dashboard"),
    path("fuel/", views.fuel_report, name="fuel_report"),

    path("maintenance/", views.maintenance_report, name="maintenance_report"),
    path("revenue/", views.revenue_report, name="revenue_report"),
    path("fuel/pdf/", views.fuel_report_pdf, name="fuel_report_pdf"),
    path("maintenance/pdf/", views.maintenance_report_pdf, name="maintenance_report_pdf"),
    path("revenue/pdf/", views.revenue_report_pdf, name="revenue_report_pdf"),
    path("ai-help/", views.ai_help_report, name="ai_help_report"),
]
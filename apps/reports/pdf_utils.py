from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


def build_fuel_pdf(response, fuels, summary, start_date="", end_date="",
                   selected_vehicle=""):

    doc = SimpleDocTemplate(
        response,
        pagesize=landscape(A4),
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=18,
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=9,
        textColor=colors.grey,
        spaceAfter=15,
    )

    normal_style = ParagraphStyle(
        "ReportNormal",
        parent=styles["Normal"],
        fontSize=8,
    )

    elements = []

    # ---------------------------------
    # Header
    # ---------------------------------

    elements.append(
        Paragraph(
            "SMART BUS CHARTER SYSTEM",
            title_style
        )
    )

    elements.append(
        Paragraph(
            "Fuel Usage Report",
            subtitle_style
        )
    )

    # ---------------------------------
    # Filters
    # ---------------------------------

    filter_text = "Filters: "

    if selected_vehicle:
        filter_text += f"Vehicle ID: {selected_vehicle} | "

    if start_date:
        filter_text += f"From: {start_date} | "

    if end_date:
        filter_text += f"To: {end_date}"

    if filter_text == "Filters: ":
        filter_text += "All Records"

    elements.append(
        Paragraph(
            filter_text,
            normal_style
        )
    )

    elements.append(Spacer(1, 8))

    # ---------------------------------
    # Summary
    # ---------------------------------

    summary_data = [
        [
            "Total Fuel Used",
            "Total Fuel Cost",
            "Average Price / Litre",
            "Total Refills",
        ],
        [
            f"{summary.get('total_litres') or 0:.2f} L",
            f"RM {summary.get('total_cost') or 0:.2f}",
            f"RM {summary.get('average_price') or 0:.2f}",
            str(summary.get("total_refills") or 0),
        ],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[
            65 * mm,
            65 * mm,
            65 * mm,
            65 * mm,
        ],
    )

    summary_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#475569")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ])
    )

    elements.append(summary_table)

    elements.append(Spacer(1, 15))

    # ---------------------------------
    # Fuel Records
    # ---------------------------------

    table_data = [
        [
            "Date",
            "Vehicle",
            "Fuel Type",
            "Litres",
            "Price/L",
            "Total Cost",
            "Fuel Station",
            "Mileage",
        ]
    ]

    for fuel in fuels:

        table_data.append([
            fuel.refill_date.strftime("%d %b %Y"),
            fuel.vehicle.registration_number,
            fuel.fuel_type,
            f"{fuel.litres:.2f}",
            f"RM {fuel.price_per_litre:.2f}",
            f"RM {fuel.total_cost:.2f}",
            fuel.fuel_station,
            f"{fuel.mileage:,} km",
        ])

    fuel_table = Table(
        table_data,
        repeatRows=1,
        colWidths=[
            27 * mm,
            30 * mm,
            28 * mm,
            22 * mm,
            25 * mm,
            28 * mm,
            55 * mm,
            30 * mm,
        ],
    )

    fuel_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4ed8")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                colors.white,
                colors.HexColor("#f8fafc"),
            ]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ])
    )

    elements.append(fuel_table)

    elements.append(Spacer(1, 12))

    elements.append(
        Paragraph(
            "Generated by Smart Bus Charter System",
            subtitle_style
        )
    )

    doc.build(elements)


def build_maintenance_pdf(
    response,
    records,
    total_records,
    total_cost,
    completed_count,
    scheduled_count,
    in_progress_count,
    cancelled_count,
    start_date="",
    end_date="",
    selected_vehicle="",
    selected_type="",
):
    doc = SimpleDocTemplate(
        response,
        pagesize=landscape(A4),
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "MaintenanceReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=18,
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "MaintenanceReportSubtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=9,
        textColor=colors.grey,
        spaceAfter=15,
    )

    normal_style = ParagraphStyle(
        "MaintenanceReportNormal",
        parent=styles["Normal"],
        fontSize=8,
    )

    elements = []

    # ---------------------------------
    # Header
    # ---------------------------------

    elements.append(
        Paragraph(
            "SMART BUS CHARTER SYSTEM",
            title_style
        )
    )

    elements.append(
        Paragraph(
            "Maintenance Report",
            subtitle_style
        )
    )

    # ---------------------------------
    # Filters
    # ---------------------------------

    filters = []

    if selected_vehicle:
        filters.append(f"Vehicle ID: {selected_vehicle}")

    if selected_type:
        filters.append(f"Maintenance Type: {selected_type}")

    if start_date:
        filters.append(f"From: {start_date}")

    if end_date:
        filters.append(f"To: {end_date}")

    filter_text = (
        "Filters: " + " | ".join(filters)
        if filters
        else "Filters: All Records"
    )

    elements.append(
        Paragraph(
            filter_text,
            normal_style
        )
    )

    elements.append(Spacer(1, 8))

    # ---------------------------------
    # Summary
    # ---------------------------------

    summary_data = [
        [
            "Total Records",
            "Total Cost",
            "Completed",
            "Scheduled",
            "In Progress",
            "Cancelled",
        ],
        [
            str(total_records),
            f"RM {total_cost:.2f}",
            str(completed_count),
            str(scheduled_count),
            str(in_progress_count),
            str(cancelled_count),
        ],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[
            42 * mm,
            48 * mm,
            42 * mm,
            42 * mm,
            42 * mm,
            42 * mm,
        ],
    )

    summary_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#f1f5f9")
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.HexColor("#475569")
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "FONTNAME",
                (0, 1),
                (-1, 1),
                "Helvetica-Bold"
            ),
            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER"
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.5,
                colors.lightgrey
            ),
            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.25,
                colors.lightgrey
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                7
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                7
            ),
        ])
    )

    elements.append(summary_table)

    elements.append(Spacer(1, 15))

    # ---------------------------------
    # Maintenance Records
    # ---------------------------------

    table_data = [
        [
            "Date",
            "Vehicle",
            "Maintenance Type",
            "Workshop",
            "Mileage",
            "Cost",
            "Status",
            "Next Service",
        ]
    ]

    for record in records:

        next_service = (
            record.next_service_date.strftime("%d %b %Y")
            if record.next_service_date
            else "-"
        )

        table_data.append([
            record.service_date.strftime("%d %b %Y"),
            record.vehicle.registration_number,
            record.maintenance_type,
            record.workshop,
            f"{record.mileage:,} km",
            f"RM {record.cost:.2f}",
            record.status,
            next_service,
        ])

    maintenance_table = Table(
        table_data,
        repeatRows=1,
        colWidths=[
            27 * mm,
            30 * mm,
            40 * mm,
            48 * mm,
            30 * mm,
            30 * mm,
            32 * mm,
            32 * mm,
        ],
    )

    maintenance_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#1d4ed8")
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                7
            ),
            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "LEFT"
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.25,
                colors.lightgrey
            ),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.white,
                    colors.HexColor("#f8fafc"),
                ]
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
        ])
    )

    elements.append(maintenance_table)

    elements.append(Spacer(1, 12))

    elements.append(
        Paragraph(
            "Generated by Smart Bus Charter System",
            subtitle_style
        )
    )

    doc.build(elements)
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)


NAVY = colors.HexColor("#172B4D")
BLUE = colors.HexColor("#2563EB")
LIGHT_BLUE = colors.HexColor("#EFF6FF")
PALE = colors.HexColor("#F8FAFC")
BORDER = colors.HexColor("#E2E8F0")
MUTED = colors.HexColor("#64748B")
GREEN = colors.HexColor("#15803D")
LIGHT_GREEN = colors.HexColor("#DCFCE7")


def safe(value):
    """Escape database values before inserting them into ReportLab markup."""
    return escape(str(value if value not in (None, "") else "Not provided"))


def generate_payment_receipt(payment):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=19 * mm,
        leftMargin=19 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=f"Payment Receipt - {payment.booking.booking_number}",
        author="Smart Bus Charter System",
    )

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="Brand",
        fontName="Helvetica-Bold",
        fontSize=23,
        leading=27,
        textColor=BLUE,
        spaceAfter=4,
    ))

    styles.add(ParagraphStyle(
        name="SubtitleCustom",
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=MUTED,
    ))

    styles.add(ParagraphStyle(
        name="ReceiptTitleCustom",
        fontName="Helvetica-Bold",
        fontSize=17,
        leading=21,
        textColor=NAVY,
        spaceAfter=4,
    ))

    styles.add(ParagraphStyle(
        name="LabelCustom",
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=MUTED,
    ))

    styles.add(ParagraphStyle(
        name="ValueCustom",
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=13,
        textColor=NAVY,
        wordWrap="CJK",
    ))

    styles.add(ParagraphStyle(
        name="BodyCustom",
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=NAVY,
        wordWrap="CJK",
    ))

    styles.add(ParagraphStyle(
        name="SectionCustom",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=NAVY,
        spaceBefore=14,
        spaceAfter=8,
    ))

    styles.add(ParagraphStyle(
        name="AmountCustom",
        fontName="Helvetica-Bold",
        fontSize=25,
        leading=30,
        textColor=NAVY,
    ))

    styles.add(ParagraphStyle(
        name="StatusCustom",
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=GREEN,
        alignment=TA_CENTER,
    ))

    styles.add(ParagraphStyle(
        name="FooterCustom",
        fontName="Helvetica",
        fontSize=8,
        leading=12,
        textColor=MUTED,
        alignment=TA_CENTER,
    ))

    booking = payment.booking
    customer = booking.customer

    customer_name = (
        f"{getattr(customer, 'first_name', '') or ''} "
        f"{getattr(customer, 'last_name', '') or ''}"
    ).strip() or getattr(customer, "name", None) or "Customer"

    customer_email = getattr(customer, "email", None) or "Not provided"

    customer_phone = (
        getattr(customer, "phone_number", None)
        or getattr(customer, "contact_number", None)
        or getattr(customer, "phone", None)
        or "Not provided"
    )

    payment_date = (
        payment.payment_date.strftime("%d %B %Y")
        if payment.payment_date else "Not recorded"
    )

    travel_date = (
        booking.travel_date.strftime("%d %B %Y")
        if booking.travel_date else "Not specified"
    )

    departure_time = (
        booking.departure_time.strftime("%I:%M %p")
        if booking.departure_time else "Not specified"
    )

    return_date = (
        booking.return_date.strftime("%d %B %Y")
        if booking.return_date else "One-way trip"
    )

    amount = f"RM {payment.amount:,.2f}"
    story = []

    # Brand header
    brand = Table(
        [[
            [
                Paragraph("SMART BUS", styles["Brand"]),
                Paragraph(
                    "BUS CHARTER MANAGEMENT SYSTEM",
                    styles["SubtitleCustom"],
                ),
            ],
            [
                Paragraph("PAYMENT RECEIPT", styles["ReceiptTitleCustom"]),
                Paragraph(
                    f"Receipt No. SB-{payment.pk:06d}",
                    styles["SubtitleCustom"],
                ),
            ],
        ]],
        colWidths=[90 * mm, 75 * mm],
    )

    brand.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))

    story.append(brand)
    story.append(HRFlowable(
        width="100%",
        thickness=1.5,
        color=BLUE,
        spaceAfter=18,
    ))

    # Payment summary panel
    summary = Table(
        [[
            [
                Paragraph("TOTAL PAID", styles["LabelCustom"]),
                Spacer(1, 4),
                Paragraph(amount, styles["AmountCustom"]),
                Spacer(1, 4),
                Paragraph(
                    f"Payment date: {safe(payment_date)}",
                    styles["SubtitleCustom"],
                ),
            ],
            [
                Paragraph("PAYMENT STATUS", styles["LabelCustom"]),
                Spacer(1, 6),
                Paragraph(
                    safe(payment.payment_status.upper()),
                    styles["StatusCustom"],
                ),
                Spacer(1, 10),
                Paragraph("PAYMENT METHOD", styles["LabelCustom"]),
                Spacer(1, 4),
                Paragraph(
                    safe(payment.payment_method),
                    styles["ValueCustom"],
                ),
            ],
        ]],
        colWidths=[100 * mm, 65 * mm],
    )

    summary.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), LIGHT_BLUE),
        ("BACKGROUND", (1, 0), (1, 0), PALE),
        ("BOX", (0, 0), (-1, -1), 0.7, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.7, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("BACKGROUND", (1, 0), (1, 0), LIGHT_GREEN),
    ]))

    story.append(summary)

    # Transaction reference
    story.append(Spacer(1, 15))

    reference_panel = Table(
        [[
            [
                Paragraph("TRANSACTION REFERENCE", styles["LabelCustom"]),
                Spacer(1, 5),
                Paragraph(
                    f"<b>{safe(payment.transaction_id or 'Not assigned')}</b>",
                    styles["ValueCustom"],
                ),
            ],
            [
                Paragraph("BOOKING NUMBER", styles["LabelCustom"]),
                Spacer(1, 5),
                Paragraph(
                    f"<b>{safe(booking.booking_number)}</b>",
                    styles["ValueCustom"],
                ),
            ],
        ]],
        colWidths=[100 * mm, 65 * mm],
    )

    reference_panel.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.7, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.7, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 13),
        ("RIGHTPADDING", (0, 0), (-1, -1), 13),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))

    story.append(reference_panel)

    def add_section(title, rows):
        story.append(Paragraph(title, styles["SectionCustom"]))

        data = [
            [
                Paragraph(safe(label), styles["LabelCustom"]),
                Paragraph(safe(value), styles["BodyCustom"]),
            ]
            for label, value in rows
        ]

        table = Table(
            data,
            colWidths=[48 * mm, 117 * mm],
            hAlign="LEFT",
        )

        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), PALE),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))

        story.append(table)

    # Customer details
    add_section("CUSTOMER DETAILS", [
        ("Customer Name", customer_name),
        ("Email Address", customer_email),
        ("Contact Number", customer_phone),
    ])

    # Journey details
    add_section("JOURNEY DETAILS", [
        ("Pickup Location", booking.pickup_location),
        ("Destination", booking.destination),
        ("Travel Date", travel_date),
        ("Departure Time", departure_time),
        ("Return Date", return_date),
        ("Passengers", booking.passenger_count),
    ])

    # Customer's booking notes / remarks
    booking_notes = (
        getattr(booking, "remarks", None)
        or "No comments provided"
    )

    add_section("BOOKING NOTES", [
        ("Customer Comments", booking_notes),
    ])

    # Footer
    story.append(Spacer(1, 22))
    story.append(HRFlowable(
        width="100%",
        thickness=0.7,
        color=BORDER,
        spaceAfter=12,
    ))

    story.append(Paragraph(
        "<b>Thank you for choosing Smart Bus.</b><br/>"
        "Please keep this receipt for your records. If you have a question "
        "about your payment, provide your booking number and transaction "
        "reference when contacting the company.",
        styles["FooterCustom"],
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer

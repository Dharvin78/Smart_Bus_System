from io import BytesIO

from django.http import FileResponse

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


def generate_payment_receipt(payment):

    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()

    story = []

    story.append(
        Paragraph(
            "<b>SMART BUS CHARTER SYSTEM</b>",
            styles["Title"],
        )
    )

    story.append(
        Paragraph(
            "Payment Receipt",
            styles["Heading2"],
        )
    )

    story.append(Spacer(1, 20))

    booking = payment.booking

    data = [

        ["Payment ID", str(payment.id)],

        ["Booking Number", booking.booking_number],

        [
            "Customer",
            f"{booking.customer.first_name} {booking.customer.last_name}",
        ],

        ["Payment Date", str(payment.payment_date)],

        ["Payment Method", payment.payment_method],

        ["Amount", f"RM {payment.amount}"],

        ["Status", payment.payment_status],

        ["Transaction ID", payment.transaction_id or "N/A"],

    ]

    table = Table(data, colWidths=[180, 250])

    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
            ("GRID",(0,0),(-1,-1),1,colors.grey),
            ("BOTTOMPADDING",(0,0),(-1,-1),10),
            ("BACKGROUND",(0,0),(0,-1),colors.whitesmoke),
        ])
    )

    story.append(table)

    story.append(Spacer(1, 25))

    story.append(
        Paragraph(
            "Thank you for choosing Smart Bus Charter System.",
            styles["Normal"],
        )
    )

    doc.build(story)

    buffer.seek(0)

    return buffer
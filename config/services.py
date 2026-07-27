from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


def send_html_email(subject, template, context, recipient):

    html = render_to_string(template, context)

    email = EmailMultiAlternatives(
        subject=subject,
        body="",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient],
    )

    email.attach_alternative(html, "text/html")

    email.send()
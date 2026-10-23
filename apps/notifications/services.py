
from django.contrib.auth import get_user_model
from django.db import transaction

from .models import Notification, NotificationRecipient

User = get_user_model()


@transaction.atomic
def create_notification(
    users,
    title,
    message,
    category="system",
    notification_type="info",
    link="",
):
    """
    Create one notification and deliver it to the specified users.

    Duplicate recipients are removed automatically.
    Returns the created Notification, or None if no valid recipients exist.
    """

    unique_users = {}

    for user in users:
        if user and user.is_authenticated:
            unique_users[user.pk] = user

    if not unique_users:
        return None

    notification = Notification.objects.create(
        title=title,
        message=message,
        category=category,
        notification_type=notification_type,
        link=link,
    )

    NotificationRecipient.objects.bulk_create([
        NotificationRecipient(
            notification=notification,
            user=user,
        )
        for user in unique_users.values()
    ])

    return notification


def notify_customer(
    booking,
    title,
    message,
    notification_type="info",
):
    """Send an in-system notification to the booking's customer."""

    customer_user = getattr(booking.customer, "user", None)

    if not customer_user:
        return None

    return create_notification(
        users=[customer_user],
        title=title,
        message=message,
        category="booking",
        notification_type=notification_type,
        link="/bookings/my-bookings/",
    )


def notify_booking_staff(
    title,
    message,
    notification_type="info",
    link="/bookings/",
):
    """Notify authenticated Owner and Admin users."""

    staff_users = User.objects.filter(
        is_active=True,
        profile__role__in=["Owner", "Admin"],
    ).distinct()

    return create_notification(
        users=staff_users,
        title=title,
        message=message,
        category="booking",
        notification_type=notification_type,
        link=link,
    )


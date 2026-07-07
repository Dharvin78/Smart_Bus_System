from .models import Notification, NotificationRecipient


def create_notification(
    title,
    message,
    category,
    notification_type,
    recipients,
    link=""
):
    """
    Create a notification and assign it to multiple users.

    Parameters:
        title (str)
        message (str)
        category (str)
        notification_type (str)
        recipients (list[User])
        link (str)
    """

    notification = Notification.objects.create(
        title=title,
        message=message,
        category=category,
        notification_type=notification_type,
        link=link,
    )

    recipient_objects = [
        NotificationRecipient(
            notification=notification,
            user=user
        )
        for user in recipients
    ]

    NotificationRecipient.objects.bulk_create(
        recipient_objects
    )

    return notification
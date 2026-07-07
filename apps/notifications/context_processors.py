from .models import NotificationRecipient


def notification_context(request):

    if not request.user.is_authenticated:
        return {}

    notifications = (
        NotificationRecipient.objects
        .filter(user=request.user)
        .select_related("notification")
        .order_by("-notification__created_at")[:5]
    )

    unread_count = (
        NotificationRecipient.objects
        .filter(
            user=request.user,
            is_read=False
        )
        .count()
    )

    return {
        "navbar_notifications": notifications,
        "unread_notifications": unread_count,
    }
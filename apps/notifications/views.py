from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse
from .models import Notification, NotificationRecipient


@login_required
def notification_list(request):

    notifications = (
        NotificationRecipient.objects
        .filter(user=request.user)
        .select_related("notification")
        .order_by("-notification__created_at")
    )

    return render(
        request,
        "notifications/notification_list.html",
        {
            "notifications": notifications
        }
    )


@login_required
def mark_as_read(request, pk):

    notification = get_object_or_404(
        NotificationRecipient,
        pk=pk,
        user=request.user
    )

    notification.is_read = True
    notification.read_at = timezone.now()
    notification.save()

    if notification.notification.link:
        return redirect(notification.notification.link)

    return redirect("notifications:list")


@login_required
def mark_all_read(request):

    NotificationRecipient.objects.filter(
        user=request.user,
        is_read=False
    ).update(
        is_read=True,
        read_at=timezone.now()
    )

    return redirect("notifications:list")

@login_required
def notification_api(request):
    notifications = (
        NotificationRecipient.objects
        .filter(user=request.user)
        .select_related("notification")
        .order_by("-notification__created_at")[:5]
    )

    data = []

    for item in notifications:
        data.append({
            "id": item.id,
            "title": item.notification.title,
            "message": item.notification.message,
            "is_read": item.is_read,
            "url": f"/notifications/read/{item.id}/"
        })

    unread = (
        NotificationRecipient.objects
        .filter(user=request.user, is_read=False)
        .count()
    )

    return JsonResponse({
        "unread": unread,
        "notifications": data
    })
# Register your models here.
from django.contrib import admin
from .models import Notification, NotificationRecipient


class NotificationRecipientInline(admin.TabularInline):
    model = NotificationRecipient
    extra = 0


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "category",
        "notification_type",
        "created_at",
    )

    list_filter = (
        "category",
        "notification_type",
    )

    search_fields = (
        "title",
        "message",
    )

    ordering = (
        "-created_at",
    )

    inlines = [
        NotificationRecipientInline,
    ]


@admin.register(NotificationRecipient)
class NotificationRecipientAdmin(admin.ModelAdmin):

    list_display = (
        "notification",
        "user",
        "is_read",
        "read_at",
    )

    list_filter = (
        "is_read",
    )

    search_fields = (
        "notification__title",
        "user__username",
    )
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Notification(models.Model):

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    DANGER = "danger"

    TYPE_CHOICES = [
        (INFO, "Info"),
        (SUCCESS, "Success"),
        (WARNING, "Warning"),
        (DANGER, "Danger"),
    ]

    BOOKING = "booking"
    VEHICLE = "vehicle"
    CUSTOMER = "customer"
    DRIVER = "driver"
    PAYMENT = "payment"
    FUEL = "fuel"
    MAINTENANCE = "maintenance"
    AI = "ai"
    SYSTEM = "system"

    CATEGORY_CHOICES = [
        (BOOKING, "Booking"),
        (VEHICLE, "Vehicle"),
        (CUSTOMER, "Customer"),
        (DRIVER, "Driver"),
        (PAYMENT, "Payment"),
        (FUEL, "Fuel"),
        (MAINTENANCE, "Maintenance"),
        (AI, "AI Prediction"),
        (SYSTEM, "System"),
    ]

    title = models.CharField(
        max_length=200
    )

    message = models.TextField()

    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        default=SYSTEM
    )

    notification_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=INFO
    )

    link = models.CharField(
        max_length=300,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class NotificationRecipient(models.Model):

    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name="recipients"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notification_recipients"
    )

    is_read = models.BooleanField(
        default=False
    )

    read_at = models.DateTimeField(
        blank=True,
        null=True
    )

    class Meta:
        unique_together = ("notification", "user")

    def __str__(self):
        return f"{self.user.username} - {self.notification.title}"
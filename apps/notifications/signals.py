from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from apps.vehicles.models import Vehicle

from .models import Notification
from .utils import create_notification

User = get_user_model()


@receiver(post_save, sender=Vehicle)
def vehicle_created(sender, instance, created, **kwargs):
    """
    Automatically notify Owner/Admin when a vehicle is created.
    """

    if not created:
        return

    recipients = User.objects.filter(
        is_staff=True
    )

    create_notification(
        title="Vehicle Added",
        message=f"{instance.registration_number} has been added.",
        category=Notification.VEHICLE,
        notification_type=Notification.SUCCESS,
        recipients=recipients,
        link="/vehicles/",
    )
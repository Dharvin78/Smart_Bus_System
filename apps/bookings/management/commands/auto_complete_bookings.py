
from django.core.management.base import BaseCommand

from apps.bookings.auto_completion_services import complete_expired_bookings


class Command(BaseCommand):
    help = "Automatically mark finished trips as Completed."

    def handle(self, *args, **options):

        completed_count = complete_expired_bookings()

        self.stdout.write(
            self.style.SUCCESS(
                f"Automatic booking completion finished. "
                f"{completed_count} booking(s) marked as Completed."
            )
        )

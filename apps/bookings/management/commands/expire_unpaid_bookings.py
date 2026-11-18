
from django.core.management.base import BaseCommand

from apps.bookings.availability_services import (
    expire_unpaid_confirmed_bookings,
)


class Command(BaseCommand):
    help = "Automatically cancel confirmed bookings with expired unpaid payments."

    def add_arguments(self, parser):
        parser.add_argument(
            "--execute",
            action="store_true",
            help="Apply cancellations instead of performing a dry run.",
        )

    def handle(self, *args, **options):
        execute = options["execute"]

        cancelled = expire_unpaid_confirmed_bookings(
            dry_run=not execute
        )

        if not execute:
            self.stdout.write(
                self.style.WARNING(
                    "DRY RUN: No database records were modified."
                )
            )

        for booking_number in cancelled:
            self.stdout.write(
                f"{'Cancelled' if execute else 'Eligible'}: "
                f"{booking_number}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Total {'cancelled' if execute else 'eligible'} "
                f"bookings: {len(cancelled)}"
            )
        )

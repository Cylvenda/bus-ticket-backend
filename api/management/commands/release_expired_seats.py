from django.core.management.base import BaseCommand
from django.utils import timezone
from api.models import Booking


class Command(BaseCommand):
    help = "Release expired held seats"

    def handle(self, *args, **kwargs):
        now = timezone.now()

        expired_bookings = Booking.objects.filter(
            status="HELD", hold_expires_at__lt=now
        )

        count = expired_bookings.update(status="CANCELLED")

        self.stdout.write(
            self.style.SUCCESS(f"Successfully released {count} expired held seats")
        )

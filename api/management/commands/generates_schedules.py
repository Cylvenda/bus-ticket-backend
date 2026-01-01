from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from api.models import ScheduleTemplate, Schedule, BusAssignment, Bus


class Command(BaseCommand):
    help = "Generate schedules from templates for the next N days"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Number of days to generate schedules for",
        )

    def handle(self, *args, **options):
        days = options["days"]
        today = timezone.now().date()

        # Get all active templates
        templates = ScheduleTemplate.objects.filter(is_active=True)

        created_count = 0

        for template in templates:
            for day_offset in range(days):
                travel_date = today + timedelta(days=day_offset)

                # Check if schedule already exists
                if Schedule.objects.filter(
                    template=template, travel_date=travel_date
                ).exists():
                    continue

                # Create the schedule
                schedule = Schedule.objects.create(
                    template=template,
                    travel_date=travel_date,
                    departure_time=template.departure_time,
                    arrival_time=template.arrival_time,
                    price=template.base_price,
                    status="ACTIVE",
                )

                # Assign buses to this schedule
                # Get available buses for this route's company (or all active buses)
                available_buses = Bus.objects.filter(is_active=True)[
                    :2
                ]  # Assign 2 buses per schedule

                for bus in available_buses:
                    BusAssignment.objects.create(
                        schedule=schedule,
                        bus=bus,
                        available_seats=bus.total_seats,
                        status="ACTIVE",
                    )

                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {created_count} schedules for the next {days} days"
            )
        )

from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import Schedule, BusAssignment, Bus


class Command(BaseCommand):
    help = "Assign buses to existing schedules that don't have bus assignments"

    def handle(self, *args, **options):
        with transaction.atomic():
            self.stdout.write("Assigning buses to existing schedules...")
            
            # Get all active buses
            buses = Bus.objects.filter(is_active=True)
            if not buses.exists():
                self.stdout.write(
                    self.style.ERROR("No active buses found. Please create buses first.")
                )
                return
            
            # Get schedules without bus assignments
            schedules_without_buses = Schedule.objects.filter(bus_assignments__isnull=True)
            
            if not schedules_without_buses.exists():
                self.stdout.write(
                    self.style.SUCCESS("All schedules already have bus assignments.")
                )
                return
            
            created_assignments = 0
            bus_index = 0
            total_buses = buses.count()
            
            for schedule in schedules_without_buses:
                # Assign 2 buses per schedule
                for i in range(2):
                    bus = buses[bus_index % total_buses]
                    
                    BusAssignment.objects.get_or_create(
                        schedule=schedule,
                        bus=bus,
                        defaults={
                            "available_seats": bus.seat_layout.total_seats
                        }
                    )
                    
                    created_assignments += 1
                    bus_index += 1
                    
                    self.stdout.write(f"Assigned {bus.plate_number} to schedule {schedule}")
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully created {created_assignments} bus assignments"
                )
            )

from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import BusCompany, SeatLayout, Bus


class Command(BaseCommand):
    help = "Create a single Tanzania bus company with multiple buses"

    def handle(self, *args, **options):
        with transaction.atomic():
            self.stdout.write("Creating single Tanzania bus company...")
            
            # Get or create seat layout
            seat_layout = self.get_or_create_seat_layout()
            
            # Create or update the main bus company
            company, created = BusCompany.objects.update_or_create(
                name="Tanzania Express",
                defaults={
                    "license_number": "TZ-2024-001",
                    "contact_email": "info@tzexpress.co.tz",
                    "contact_phone": "+255 22 211 1234",
                    "address": "Ubungo Bus Terminal, Dar es Salaam, Tanzania"
                }
            )
            
            if created:
                self.stdout.write(f"Created company: {company}")
            else:
                self.stdout.write(f"Updated existing company: {company}")
            
            # Create 5 buses for this company
            buses_data = [
                {"plate": "TZ001", "type": "Luxury Coach", "amenities": "AC,WIFI,USB Charging,Reclining Seats,TV,Toilet"},
                {"plate": "TZ002", "type": "Executive Coach", "amenities": "AC,WIFI,USB Charging,Reclining Seats,TV,Snacks"},
                {"plate": "TZ003", "type": "Standard Coach", "amenities": "AC,WIFI,USB Charging,Reclining Seats"},
                {"plate": "TZ004", "type": "Business Class", "amenities": "AC,WIFI,USB Charging,Reclining Seats,TV,Meals,Toilet"},
                {"plate": "TZ005", "type": "Economy Coach", "amenities": "AC,USB Charging,Reclining Seats"}
            ]
            
            created_buses = 0
            
            for bus_data in buses_data:
                bus, bus_created = Bus.objects.get_or_create(
                    plate_number=bus_data["plate"],
                    defaults={
                        "company": company,
                        "bus_type": bus_data["type"],
                        "amenities": bus_data["amenities"],
                        "seat_layout": seat_layout,
                        "is_active": True
                    }
                )
                
                if bus_created:
                    created_buses += 1
                    self.stdout.write(f"  Created bus: {bus}")
                else:
                    self.stdout.write(f"  Bus already exists: {bus}")
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully setup:\n"
                    f"- Company: {company.name}\n"
                    f"- Total buses: {company.buses.count()}\n"
                    f"- New buses created: {created_buses}"
                )
            )

    def get_or_create_seat_layout(self):
        """Get or create a default seat layout"""
        layout_data = {
            "rows": [
                ["A1", "A2", None, "A3", "A4"],
                ["B1", "B2", None, "B3", "B4"],
                ["C1", "C2", None, "C3", "C4"],
                ["D1", "D2", None, "D3", "D4"],
                ["E1", "E2", None, "E3", "E4"],
                ["F1", "F2", None, "F3", "F4"],
                ["G1", "G2", None, "G3", "G4"],
                ["H1", "H2", None, "H3", "H4"],
                ["I1", "I2", None, "I3", "I4"],
                ["J1", "J2", None, "J3", "J4"]
            ]
        }
        
        seat_layout, created = SeatLayout.objects.get_or_create(
            name="Standard Bus Layout",
            defaults={
                "layout": layout_data,
                "total_seats": 40,
                "is_active": True
            }
        )
        
        if created:
            self.stdout.write(f"Created seat layout: {seat_layout}")
        
        return seat_layout

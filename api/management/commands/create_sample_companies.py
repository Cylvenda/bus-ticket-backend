from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import BusCompany, SeatLayout, Bus


class Command(BaseCommand):
    help = "Create sample Tanzania bus companies and buses"

    def handle(self, *args, **options):
        with transaction.atomic():
            self.stdout.write("Creating sample Tanzania bus companies and buses...")
            
            # Get or create seat layout
            seat_layout = self.get_or_create_seat_layout()
            
            # Tanzania popular bus companies
            companies_data = [
                {
                    "name": "Dar Express",
                    "license_number": "DL-2023-001",
                    "contact_email": "info@darespress.co.tz",
                    "contact_phone": "+255 22 211 1234",
                    "address": "Dar es Salaam, Tanzania"
                },
                {
                    "name": "Kilimanjaro Express",
                    "license_number": "KL-2023-002", 
                    "contact_email": "info@kilimanjaroexpress.co.tz",
                    "contact_phone": "+255 27 275 1234",
                    "address": "Arusha, Tanzania"
                },
                {
                    "name": "Sumry High Class",
                    "license_number": "SM-2023-003",
                    "contact_email": "info@sumry.co.tz", 
                    "contact_phone": "+255 22 284 5678",
                    "address": "Dar es Salaam, Tanzania"
                },
                {
                    "name": "City Hoppa",
                    "license_number": "CH-2023-004",
                    "contact_email": "info@cityhoppa.co.tz",
                    "contact_phone": "+255 22 211 9999", 
                    "address": "Dar es Salaam, Tanzania"
                },
                {
                    "name": "Raha Coach",
                    "license_number": "RC-2023-005",
                    "contact_email": "info@rahacoach.co.tz",
                    "contact_phone": "+255 22 284 1111",
                    "address": "Dar es Salaam, Tanzania"
                }
            ]
            
            created_companies = 0
            created_buses = 0
            
            for company_data in companies_data:
                company, created = BusCompany.objects.get_or_create(
                    name=company_data["name"],
                    defaults={
                        "license_number": company_data["license_number"],
                        "contact_email": company_data["contact_email"],
                        "contact_phone": company_data["contact_phone"],
                        "address": company_data["address"]
                    }
                )
                
                if created:
                    created_companies += 1
                    self.stdout.write(f"Created company: {company}")
                    
                    # Create 2-3 buses for each company
                    buses_to_create = min(3, max(2, len(company_data["name"]) // 2))
                    for i in range(buses_to_create):
                        bus_plate = f"{company.name[:3].upper()}{str(i+1).zfill(3)}"
                        bus, bus_created = Bus.objects.get_or_create(
                            plate_number=bus_plate,
                            defaults={
                                "company": company,
                                "bus_type": "Luxury Coach",
                                "amenities": "AC,WIFI,USB Charging,Reclining Seats,TV",
                                "seat_layout": seat_layout,
                                "is_active": True
                            }
                        )
                        
                        if bus_created:
                            created_buses += 1
                            self.stdout.write(f"  Created bus: {bus}")
                else:
                    self.stdout.write(f"Company already exists: {company}")
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully created:\n"
                    f"- {created_companies} new bus companies\n"
                    f"- {created_buses} new buses"
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

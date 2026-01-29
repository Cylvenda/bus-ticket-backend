from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import BusCompany, Route, RouteStop, ScheduleTemplate, SeatLayout, Bus


class Command(BaseCommand):
    help = "Seed Tanzania popular routes and route stops for existing bus companies"

    def handle(self, *args, **options):
        with transaction.atomic():
            self.stdout.write("Starting to seed Tanzania popular routes...")
            
            # Get existing bus companies
            companies = BusCompany.objects.all()
            if not companies.exists():
                self.stdout.write(
                    self.style.ERROR("No bus companies found. Please create bus companies first.")
                )
                return
            
            # Get or create default seat layout
            seat_layout = self.get_or_create_seat_layout()
            
            # Get existing buses
            buses = Bus.objects.filter(is_active=True)
            if not buses.exists():
                self.stdout.write(
                    self.style.ERROR("No active buses found. Please create buses first.")
                )
                return
            
            # Tanzania popular routes with stops
            routes_data = [
                {
                    "origin": "Dar es Salaam",
                    "destination": "Arusha",
                    "distance_km": 620,
                    "estimated_duration_minutes": 600,
                    "stops": [
                        ("Morogoro", 120, 125),
                        ("Dodoma", 300, 310),
                        ("Babati", 480, 490),
                        ("Moshi", 580, 590)
                    ]
                },
                {
                    "origin": "Dar es Salaam",
                    "destination": "Mwanza",
                    "distance_km": 1140,
                    "estimated_duration_minutes": 720,
                    "stops": [
                        ("Morogoro", 120, 125),
                        ("Dodoma", 300, 310),
                        ("Singida", 450, 460),
                        ("Shinyanga", 900, 910)
                    ]
                },
                {
                    "origin": "Dar es Salaam",
                    "destination": "Mbeya",
                    "distance_km": 850,
                    "estimated_duration_minutes": 660,
                    "stops": [
                        ("Morogoro", 120, 125),
                        ("Iringa", 500, 510),
                        ("Mafinga", 600, 610),
                        ("Makambako", 700, 710)
                    ]
                },
                {
                    "origin": "Dar es Salaam",
                    "destination": "Tanga",
                    "distance_km": 350,
                    "estimated_duration_minutes": 300,
                    "stops": [
                        ("Chalinze", 100, 105),
                        ("Korogwe", 200, 205),
                        ("Mombo", 250, 255)
                    ]
                },
                {
                    "origin": "Dar es Salaam",
                    "destination": "Moshi",
                    "distance_km": 570,
                    "estimated_duration_minutes": 540,
                    "stops": [
                        ("Morogoro", 120, 125),
                        ("Dodoma", 300, 310),
                        ("Babati", 480, 490)
                    ]
                },
                {
                    "origin": "Arusha",
                    "destination": "Mwanza",
                    "distance_km": 520,
                    "estimated_duration_minutes": 480,
                    "stops": [
                        ("Babati", 60, 65),
                        ("Singida", 200, 210),
                        ("Shinyanga", 400, 410)
                    ]
                },
                {
                    "origin": "Arusha",
                    "destination": "Mbeya",
                    "distance_km": 750,
                    "estimated_duration_minutes": 600,
                    "stops": [
                        ("Dodoma", 250, 260),
                        ("Iringa", 450, 460),
                        ("Mafinga", 550, 560)
                    ]
                },
                {
                    "origin": "Mwanza",
                    "destination": "Mbeya",
                    "distance_km": 780,
                    "estimated_duration_minutes": 660,
                    "stops": [
                        ("Shinyanga", 120, 125),
                        ("Singida", 300, 310),
                        ("Dodoma", 450, 460),
                        ("Iringa", 600, 610)
                    ]
                },
                {
                    "origin": "Dar es Salaam",
                    "destination": "Kigoma",
                    "distance_km": 1250,
                    "estimated_duration_minutes": 900,
                    "stops": [
                        ("Morogoro", 120, 125),
                        ("Dodoma", 300, 310),
                        ("Tabora", 600, 610),
                        ("Uvinza", 900, 910)
                    ]
                },
                {
                    "origin": "Dar es Salaam",
                    "destination": "Songea",
                    "distance_km": 950,
                    "estimated_duration_minutes": 720,
                    "stops": [
                        ("Morogoro", 120, 125),
                        ("Iringa", 500, 510),
                        ("Mafinga", 600, 610),
                        ("Makambako", 700, 710),
                        ("Njombe", 800, 810)
                    ]
                }
            ]
            
            created_routes = 0
            created_stops = 0
            created_templates = 0
            
            for route_data in routes_data:
                # Check if route already exists
                route, created = Route.objects.get_or_create(
                    origin=route_data["origin"],
                    destination=route_data["destination"],
                    defaults={
                        "distance_km": route_data["distance_km"],
                        "estimated_duration_minutes": route_data["estimated_duration_minutes"],
                        "is_active": True
                    }
                )
                
                if created:
                    created_routes += 1
                    self.stdout.write(f"Created route: {route}")
                    
                    # Create route stops
                    for stop_order, (stop_name, arrival_offset, departure_offset) in enumerate(route_data["stops"], 1):
                        RouteStop.objects.get_or_create(
                            route=route,
                            stop_name=stop_name,
                            stop_order=stop_order,
                            defaults={
                                "arrival_offset_min": arrival_offset,
                                "departure_offset_min": departure_offset
                            }
                        )
                        created_stops += 1
                    
                    # Create schedule templates for this route
                    templates = self.create_schedule_templates(route)
                    created_templates += len(templates)
                    
                else:
                    self.stdout.write(f"Route already exists: {route}")
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully seeded:\n"
                    f"- {created_routes} new routes\n"
                    f"- {created_stops} route stops\n"
                    f"- {created_templates} schedule templates"
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

    def create_schedule_templates(self, route):
        """Create schedule templates for a route"""
        templates = []
        
        # Different departure times for different routes
        if route.destination in ["Arusha", "Moshi"]:
            departure_times = [("06:00", "16:00"), ("08:00", "18:00"), ("22:00", "08:00")]
            base_prices = [45000, 50000, 48000]  # TZS
        elif route.destination == "Mwanza":
            departure_times = [("05:30", "17:30"), ("07:00", "19:00"), ("21:00", "09:00")]
            base_prices = [65000, 70000, 68000]  # TZS
        elif route.destination == "Mbeya":
            departure_times = [("06:30", "18:30"), ("08:30", "20:30"), ("23:00", "11:00")]
            base_prices = [55000, 60000, 58000]  # TZS
        elif route.destination == "Tanga":
            departure_times = [("07:00", "12:00"), ("09:00", "14:00"), ("14:00", "19:00")]
            base_prices = [25000, 28000, 30000]  # TZS
        elif route.destination == "Kigoma":
            departure_times = [("05:00", "20:00"), ("06:00", "21:00")]
            base_prices = [85000, 90000]  # TZS
        elif route.destination == "Songea":
            departure_times = [("06:00", "18:00"), ("08:00", "20:00")]
            base_prices = [65000, 70000]  # TZS
        else:
            departure_times = [("07:00", "17:00"), ("09:00", "19:00")]
            base_prices = [40000, 45000]  # TZS
        
        for i, (departure_time, arrival_time) in enumerate(departure_times):
            template, created = ScheduleTemplate.objects.get_or_create(
                route=route,
                departure_time=departure_time,
                arrival_time=arrival_time,
                defaults={
                    "base_price": base_prices[i],
                    "is_active": True
                }
            )
            
            if created:
                templates.append(template)
                self.stdout.write(f"  Created template: {template}")
        
        return templates

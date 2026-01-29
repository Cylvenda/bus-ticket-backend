from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import BusCompany, Bus


class Command(BaseCommand):
    help = "Keep only one bus company and remove others"

    def handle(self, *args, **options):
        with transaction.atomic():
            self.stdout.write("Cleaning up to keep only one bus company...")
            
            # Get all companies
            companies = BusCompany.objects.all()
            
            if companies.count() <= 1:
                self.stdout.write(
                    self.style.SUCCESS("Only one or zero companies exist. No cleanup needed.")
                )
                return
            
            # Keep the first company (Dar Express) and remove others
            company_to_keep = companies.first()
            companies_to_remove = companies.exclude(id=company_to_keep.id)
            
            removed_count = 0
            removed_buses = 0
            
            for company in companies_to_remove:
                # Count buses before removing
                bus_count = company.buses.count()
                removed_buses += bus_count
                
                # Remove the company (this will cascade delete buses)
                company.delete()
                removed_count += 1
                
                self.stdout.write(f"Removed company: {company.name} (with {bus_count} buses)")
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully cleaned up:\n"
                    f"- Kept company: {company_to_keep.name}\n"
                    f"- Removed {removed_count} companies\n"
                    f"- Removed {removed_buses} buses\n"
                    f"- Remaining buses: {company_to_keep.buses.count()}"
                )
            )

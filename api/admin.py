from django.contrib import admin
from django.contrib import admin
from django.utils import timezone
from datetime import timedelta
from .models import (
    BusCompany,
    Route,
    RouteStop,
    Bus,
    Schedule,
    ScheduleTemplate,
    Booking,
    PromoCode,
    Passenger,
    BusAssignment,
)


class ScheduleTemplateAdmin(admin.ModelAdmin):
    list_display = ["route", "departure_time", "base_price", "is_active"]
    actions = ["generate_schedules_30_days"]

    @admin.action(description="Generate schedules for next 30 days")
    def generate_schedules_30_days(self, request, queryset):
        today = timezone.now().date()
        created = 0

        for template in queryset:
            for day in range(30):
                travel_date = today + timedelta(days=day)

                schedule, created_flag = Schedule.objects.get_or_create(
                    template=template,
                    travel_date=travel_date,
                    defaults={
                        "departure_time": template.departure_time,
                        "arrival_time": template.arrival_time,
                        "price": template.base_price,
                        "status": "ACTIVE",
                    },
                )

                # Assign buses if schedule was just created
                if created_flag:
                    # Get available buses (you can customize this logic)
                    available_buses = Bus.objects.filter(is_active=True)[:2]
                    for bus in available_buses:
                        BusAssignment.objects.create(
                            schedule=schedule,
                            bus=bus,
                            available_seats=bus.total_seats,
                            status="ACTIVE",
                        )
                    created += 1

        self.message_user(request, f"{created} schedules created for the next 30 days")


admin.site.register(
    [
        BusCompany,
        Route,
        RouteStop,
        Bus,
        Schedule,
        ScheduleTemplate,
        Booking,
        PromoCode,
        Passenger,
        BusAssignment,
    ]
)

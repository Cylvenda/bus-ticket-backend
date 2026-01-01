from datetime import timedelta, date
from .models import ScheduleTemplate, Schedule


def generate_schedules_for_routes(start_date: date, end_date: date):
    templates = ScheduleTemplate.objects.all()
    current = start_date

    while current <= end_date:
        for template in templates:
            if not Schedule.objects.filter(template=template, date=current).exists():
                Schedule.objects.create(template=template)
        current += timedelta(days=1)

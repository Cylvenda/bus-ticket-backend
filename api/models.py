from django.db import models
from accounts.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Passenger


class BusCompany(models.Model):
    name = models.CharField(max_length=255)
    license_number = models.CharField(max_length=200)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Bus(models.Model):
    company = models.ForeignKey(
        BusCompany, on_delete=models.CASCADE, related_name="buses"
    )
    plate_number = models.CharField(max_length=20, unique=True)
    bus_type = models.CharField(max_length=100)
    total_seats = models.PositiveIntegerField()
    amenities = models.TextField(
        blank=True
    )  # inserted like dictionary ("AC", "WIFI", ....)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.plate_number} ({self.company.name})"


class Route(models.Model):
    origin = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    distance_km = models.PositiveIntegerField(blank=True, null=True)
    estimated_duration_minutes = models.PositiveIntegerField(null=True)

    def __str__(self):
        return f"{self.origin} → {self.destination}"


class RouteStop(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name="stops")
    stop_name = models.CharField(max_length=200)
    stop_order = models.PositiveIntegerField()
    arrival_offset_min = models.PositiveIntegerField()
    departure_offset_min = models.PositiveIntegerField()

    class Meta:
        ordering = ["stop_order"]

    def __str__(self):
        return f"{self.route} - {self.stop_name}"


class ScheduleTemplate(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name="templates")
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    base_price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.route} @ {self.departure_time}"


class Schedule(models.Model):

    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("CANCELLED", "Cancelled"),
        ("COMPLETED", "Completed"),
    ]

    template = models.ForeignKey(
        ScheduleTemplate, on_delete=models.CASCADE, related_name="schedule"
    )
    travel_date = models.DateField()

    departure_time = models.TimeField()
    arrival_time = models.TimeField()

    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="ACTIVE")

    # If price is not set, inherit from template
    def save(self, *args, **kwargs):
        if not self.price:
            self.price = self.template.base_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.template.route} | {self.travel_date}"


# bus assignment to schedule
class BusAssignment(models.Model):

    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("CANCELLED", "Cancelled"),
        ("COMPLETED", "Completed"),
    ]

    schedule = models.ForeignKey(
        Schedule, on_delete=models.CASCADE, related_name="bus_assignments"
    )
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE)
    available_seats = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="ACTIVE")

    class Meta:
        unique_together = ("schedule", "bus")

    def __str__(self):
        return f"{self.schedule} | {self.bus.plate_number}"


class Booking(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="booking",
        null=True,
        blank=True,
    )
    schedule = models.ForeignKey(
        Schedule, on_delete=models.CASCADE, related_name="booking"
    )
    bus_assignment = models.ForeignKey(
        "BusAssignment",
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    seat_number = models.PositiveIntegerField()
    price_paid = models.DecimalField(max_digits=10, decimal_places=2)

    is_paid = models.BooleanField(default=False)
    booked_at = models.DateTimeField(auto_now_add=True)

    if TYPE_CHECKING:
        passenger: "Passenger"

    class Meta:
        unique_together = ("bus_assignment", "seat_number")

    def __str__(self):
        if self.user:
            return f"{self.user.username} | {self.schedule} | Seat {self.seat_number}"
        # Access passenger email via reverse relation
        return f"Guest ({self.passenger.email}) | {self.schedule} | Seat {self.seat_number}"

    @property
    def is_guest_booking(self):
        """Check if this is a guest booking"""
        return self.user is None

    @property
    def contact_email(self):
        """Get contact email - from user or passenger"""
        if self.user:
            return self.user.email
        return self.passenger.email if hasattr(self, "passenger") else None

    @property
    def contact_phone(self):
        """Get contact phone - from passenger"""
        return self.passenger.phone if hasattr(self, "passenger") else None


class Passenger(models.Model):

    GENDER_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
    ]

    booking = models.OneToOneField(
        Booking, on_delete=models.CASCADE, related_name="passenger"
    )
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    age = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(120)])
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    nationality = models.CharField(max_length=50)
    boarding_point = models.CharField(max_length=200)
    dropping_point = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class PromoCode(models.Model):

    code = models.CharField(max_length=20, unique=True)
    description = models.TextField()

    discount_type = models.CharField(
        max_length=15,
        choices=[
            ("PERCENTAGE", "Percentage"),
            ("FIXED", "Fixed Amount"),
        ],
    )
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    max_discount = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )

    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    max_uses = models.PositiveIntegerField()
    current_uses = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    def is_valid(self):
        now = timezone.now()
        return (
            self.is_active
            and self.valid_from <= now <= self.valid_until
            and self.current_uses < self.max_uses
        )

    def __str__(self):
        return self.code

# services.py
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from decimal import Decimal

from .models import Booking, Schedule, PromoCode, Bus


@transaction.atomic
def book_seat(user, schedule, bus_assignment, seat_number, price):
    """
    Atomically book a seat on a specific bus assignment
    No need to pass guest_email/guest_phone - they'll be in Passenger model
    """
    # Check if seat is already booked
    if Booking.objects.filter(
        bus_assignment=bus_assignment, seat_number=seat_number
    ).exists():
        raise ValidationError(
            f"Seat {seat_number} is already booked on bus {bus_assignment.bus.plate_number}"
        )

    # Check if bus has available seats
    booked_count = Booking.objects.filter(
        bus_assignment=bus_assignment, is_paid=True
    ).count()

    if booked_count >= bus_assignment.bus.total_seats:
        raise ValidationError("This bus is fully booked")

    if bus_assignment.available_seats <= 0:
        raise ValidationError("No seats available on this bus")

    # Create the booking
    booking = Booking.objects.create(
        user=user,  # Can be None for guest bookings
        schedule=schedule,
        bus_assignment=bus_assignment,
        seat_number=seat_number,
        price_paid=price,
        is_paid=False,
    )

    # Decrement available seats
    bus_assignment.available_seats -= 1
    bus_assignment.save()

    return booking


# promocode service
@transaction.atomic
def apply_promo(schedule_price: Decimal, promo: PromoCode, increment_usage: bool = False) -> Decimal:
    """
    Apply promo code discount.
    If increment_usage=True, atomically increments usage count.
    """
    if promo.max_uses and promo.current_uses >= promo.max_uses:
        raise ValidationError("Promo code usage limit reached")
    
    if promo.discount_type == "PERCENTAGE":
        discount = (promo.discount_value / Decimal("100")) * schedule_price
    else:
        discount = promo.discount_value

    if promo.max_discount:
        discount = min(discount, promo.max_discount)

    final_price = max(schedule_price - discount, Decimal("0"))
    
    if increment_usage:
        # Use F() expression for atomic increment
        from django.db.models import F
        PromoCode.objects.filter(id=promo.pk).update(times_used=F('times_used') + 1)
    
    return final_price

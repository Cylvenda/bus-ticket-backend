# services.py
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.utils import timezone
from .models import Booking, Schedule, PromoCode, Bus


@transaction.atomic
def book_seat(*, user, schedule, bus_assignment, seat_number, price):
    now = timezone.now()

    # Lock any conflicting bookings
    seat_taken = (
        Booking.objects.select_for_update()
        .filter(
            bus_assignment=bus_assignment,
            seat_number=seat_number,
            status__in=["HELD", "CONFIRMED"],
        )
        .exclude(status="HELD", hold_expires_at__lt=now)
        .exists()
    )

    if seat_taken:
        raise ValidationError(f"Seat {seat_number} is already booked")

    booking = Booking.objects.create(
        user=user,  # None for guest
        schedule=schedule,
        bus_assignment=bus_assignment,
        seat_number=seat_number,
        price_paid=price,
        status="CONFIRMED",  # or HELD depending on flow
    )

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

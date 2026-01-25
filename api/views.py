from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from .models import (
    BusAssignment,
    BusCompany,
    Bus,
    Route,
    RouteStop,
    ScheduleTemplate,
    Schedule,
    Passenger,
    PromoCode,
    Booking,
)
from .serializers import (
    BookingSerializer,
    BusCompanySerializer,
    BusSerializer,
    RouteSerializer,
    RouteStopSerializer,
    ScheduleTemplateSerializer,
    ScheduleSerializer,
    ScheduleSearchSerializer,
    BookingCreateSerializer,
    SearchRouteSerializer,
    BookingCreateSerializer,
)
from .services import apply_promo, book_seat
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from typing import cast, Any


HOLD_DURATION_MINUTES = 10


class BusCompanyViewSet(ModelViewSet):
    serializer_class = BusCompanySerializer
    queryset = BusCompany.objects.all()
    permission_classes = [IsAuthenticated]


class BusViewSet(ModelViewSet):
    serializer_class = BusSerializer
    queryset = Bus.objects.all()
    permission_classes = [IsAuthenticated]


class RouteViewSet(ModelViewSet):
    serializer_class = RouteSerializer
    queryset = Route.objects.all()
    # permission_classes = [IsAuthenticated]


class RouteStopViewSet(ModelViewSet):
    serializer_class = RouteStopSerializer
    queryset = RouteStop.objects.all()
    # permission_classes = [IsAuthenticated]


class ScheduleTemplateViewSet(ModelViewSet):
    serializer_class = ScheduleTemplateSerializer
    queryset = ScheduleTemplate.objects.all()
    # permission_classes = [IsAuthenticated]


class ScheduleViewSet(ModelViewSet):
    serializer_class = ScheduleSerializer
    queryset = Schedule.objects.all()
    # permission_classes = [IsAuthenticated]


@api_view(["GET"])
def get_active_routes(request):
    routes = Route.objects.filter(is_active=True)

    if not routes.exists():
        return Response({"detail": "No active routes available"}, status=404)

    serializer = RouteSerializer(routes, many=True)
    return Response(serializer.data)


class SearchRouteView(APIView):

    def post(self, request):
        serializer = SearchRouteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        assert isinstance(validated_data, dict)

        origin = validated_data["origin"]
        destination = validated_data["destination"]
        travel_date = validated_data["date"]

        # First check if route templates exist
        templates_exist = ScheduleTemplate.objects.filter(
            route__origin__icontains=origin,
            route__destination__icontains=destination,
            is_active=True,
        ).exists()

        if not templates_exist:
            return Response(
                {
                    "success": False,
                    "message": f"Sorry, we don't have buses operating between {origin} and {destination}.",
                    "suggestion": "Please check the route names or try a different route.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Fetch schedules
        schedules = (
            Schedule.objects.filter(
                template__route__origin__icontains=origin,
                template__route__destination__icontains=destination,
                travel_date=travel_date,
                bus_assignments__bus__is_active=True,
            )
            .select_related("template__route")
            .prefetch_related("bus_assignments__bus")
            .annotate(booked_seats=Count("booking", filter=Q(booking__is_paid=True)))
            .order_by("departure_time")
            .distinct()
        )

        # Check if no schedules found
        if not schedules.exists():
            return Response(
                {
                    "success": False,
                    "message": f"No buses available for {travel_date.strftime('%d-%m-%Y')}.",
                    "suggestion": "Try selecting a different date or check back later.",
                    "details": {
                        "origin": origin,
                        "destination": destination,
                        "date": travel_date.strftime("%d-%m-%Y"),
                    },
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        response_serializer = ScheduleSearchSerializer(schedules, many=True)
        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )


class RouteStopsView(APIView):
    
    def get(self, request, route_id):
        stops = RouteStop.objects.filter(route_id=route_id).order_by("stop_order")

        if not stops.exists():
            return Response(
                {"detail": "No stops found for this route"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = RouteStopSerializer(stops, many=True)
        return Response(serializer.data)


@api_view(["POST"])
def hold_seat(request):
    """
    Hold a seat temporarily for a user or guest.
    Returns booking ID and hold expiry time.
    """
    user = request.user if request.user.is_authenticated else None

    schedule_id = request.data.get("schedule_id")
    bus_assignment_id = request.data.get("bus_assignment_id")
    seat_number = request.data.get("seat_number")

    if not all([schedule_id, bus_assignment_id, seat_number]):
        return Response(
            {"detail": "schedule_id, bus_assignment_id and seat_number are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    expires_at = timezone.now() + timedelta(minutes=HOLD_DURATION_MINUTES)
    now = timezone.now()

    try:
        with transaction.atomic():
            # Check if the seat is already HELD or CONFIRMED (ignore expired HELD)
            seat_taken = (
                Booking.objects.select_for_update()
                .filter(
                    bus_assignment_id=bus_assignment_id,
                    seat_number=seat_number,
                    status__in=["HELD", "CONFIRMED"],
                )
                .exclude(status="HELD", hold_expires_at__lt=now)
                .exists()
            )

            if seat_taken:
                return Response(
                    {"detail": "Seat already booked or held"},
                    status=status.HTTP_409_CONFLICT,
                )

            # Get the schedule price
            try:
                schedule = Schedule.objects.get(id=schedule_id)
            except Schedule.DoesNotExist:
                return Response(
                    {"detail": "Schedule not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Create the HELD booking
            booking = Booking.objects.create(
                user=user,
                schedule_id=schedule_id,
                bus_assignment_id=bus_assignment_id,
                seat_number=seat_number,
                price_paid=schedule.price,
                status="HELD",
                hold_expires_at=expires_at,
            )

    except IntegrityError:
        # Last line of defense against race conditions
        return Response(
            {"detail": "Seat already booked or held"},
            status=status.HTTP_409_CONFLICT,
        )

    return Response(
        {
            "booking_id": booking.pk,
            "hold_expires_at": booking.hold_expires_at,
        },
        status=status.HTTP_201_CREATED,
    )


class CreateBookingView(APIView):
    # permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = BookingCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = cast(dict[str, Any], serializer.validated_data)

        schedule_id = validated_data["schedule_id"]
        bus_assignment_id = validated_data["bus_assignment_id"]
        seat_number = validated_data["seat_number"]
        passenger_data = validated_data["passenger"]
        promo_code = validated_data.get("promo_code")

        # Validate schedule
        try:
            schedule = Schedule.objects.select_related("template").get(
                id=schedule_id,
            )
        except Schedule.DoesNotExist:
            return Response(
                {"detail": "Schedule not found or inactive"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Validate bus assignment
        try:
            bus_assignment = BusAssignment.objects.select_related("bus").get(
                id=bus_assignment_id,
                schedule=schedule,
            )
        except BusAssignment.DoesNotExist:
            return Response(
                {"detail": "Bus not found for this schedule"},
                status=status.HTTP_404_NOT_FOUND,
            )

        seat_layout = bus_assignment.bus.seat_layout
        valid_seats = seat_layout.get_all_seats()

        if seat_number not in valid_seats:
            return Response(
                {"detail": "Invalid seat number for this bus"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        final_price = schedule.price
        promo = None

        # Validate and apply promo code
        if promo_code:
            try:
                # Lock promo code row to prevent concurrent over-usage
                promo = PromoCode.objects.select_for_update().get(code=promo_code)
                if not promo.is_valid():
                    return Response(
                        {"detail": "Invalid or expired promo code"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                final_price = apply_promo(final_price, promo, increment_usage=False)
            except PromoCode.DoesNotExist:
                return Response(
                    {"detail": "Invalid promo code"}, status=status.HTTP_400_BAD_REQUEST
                )

        user = request.user if request.user.is_authenticated else None

        # Atomic seat booking
        try:
            booking = book_seat(
                user=user,
                schedule=schedule,
                bus_assignment=bus_assignment,
                seat_number=seat_number,
                price=final_price,
            )
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Create passenger
        Passenger.objects.create(booking=booking, **passenger_data)

        # Increment promo usage only after successful booking
        if promo:
            promo.current_uses += 1
            promo.save()

        return Response(
            {
                "detail": "Booking successful",
                "booking_id": booking.pk,
                "schedule": {
                    "origin": str(schedule.template.route.origin),
                    "destination": str(schedule.template.route.destination),
                    "date": schedule.travel_date.strftime("%d-%m-%Y"),
                    "departure_time": schedule.departure_time.strftime("%H:%M"),
                    "arrival_time": schedule.arrival_time.strftime("%H:%M"),
                },
                "bus": {
                    "plate_number": bus_assignment.bus.plate_number,
                    "company": bus_assignment.bus.company.name,
                },
                "seat_number": seat_number,
                "price_paid": str(final_price),
                "original_price": str(schedule.price),
                "discount": str(schedule.price - final_price) if promo else "0.00",
                "passenger": {
                    "first_name": booking.passenger.first_name,
                    "last_name": booking.passenger.last_name,
                    "email": booking.passenger.email,
                    "phone": booking.passenger.phone,
                    "age_group": booking.passenger.age_group,
                    "gender": booking.passenger.gender,
                    "nationality": booking.passenger.nationality,
                },
            },
            status=status.HTTP_201_CREATED,
        )


@api_view(["POST"])
def get_seat_status(request):
    """
    Returns held seats and booked seats separately
    """
    schedule_id = request.data.get("schedule_id")
    bus_assignment_id = request.data.get("bus_assignment_id")

    if not schedule_id or not bus_assignment_id:
        return Response(
            {"detail": "schedule_id and bus_assignment_id are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    now = timezone.now()

    held_seats = Booking.objects.filter(
        schedule_id=schedule_id,
        bus_assignment_id=bus_assignment_id,
        status="HELD",
        hold_expires_at__gt=now,
    ).values_list("seat_number", flat=True)

    booked_seats = Booking.objects.filter(
        schedule_id=schedule_id,
        bus_assignment_id=bus_assignment_id,
        status="CONFIRMED",
    ).values_list("seat_number", flat=True)

    return Response(
        {
            "held_seats": list(held_seats),
            "booked_seats": list(booked_seats),
        }
    )

class BookingListView(APIView):
    def get(self, request):
        bookings = (
            Booking.objects.select_related(
                "schedule",
                "schedule__template",
                "schedule__template__route",
                "bus_assignment",
                "bus_assignment__bus",
                "bus_assignment__bus__company",
                "bus_assignment__bus__seat_layout",
                "passenger",
                "user",
            )
            .filter(status="CONFIRMED")
            .order_by("-id")
        )

        paginator = PageNumberPagination()
        paginator.page_size = 20

        page = paginator.paginate_queryset(bookings, request)

        serializer = BookingSerializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)

class UserBookingListView(APIView):
    """
    View to return bookings for the authenticated user only
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Filter bookings by the authenticated user
        bookings = (
            Booking.objects.select_related(
                "schedule",
                "schedule__template",
                "schedule__template__route",
                "bus_assignment",
                "bus_assignment__bus",
                "bus_assignment__bus__company",
                "bus_assignment__bus__seat_layout",
                "passenger",
                "user",
            )
            .filter(user=request.user)  # Filter by authenticated user
            .order_by("-id")
        )

        # Optional: Filter by status if provided in query params
        status = request.query_params.get("status", None)
        if status:
            bookings = bookings.filter(status=status.upper())

        paginator = PageNumberPagination()
        paginator.page_size = 20

        page = paginator.paginate_queryset(bookings, request)

        serializer = BookingSerializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)


class UserBookingStatsView(APIView):
    """
    View to return booking statistics for the authenticated user
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_bookings = Booking.objects.filter(user=request.user)

        stats = {
            "total_bookings": user_bookings.count(),
            "pending": user_bookings.filter(status="PENDING").count(),
            "confirmed": user_bookings.filter(status="CONFIRMED").count(),
            "cancelled": user_bookings.filter(status="CANCELLED").count(),
            "completed": user_bookings.filter(status="COMPLETED").count(),
        }

        return Response(stats)
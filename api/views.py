from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
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
)
from .serializers import (
    BusCompanySerializer,
    BusSerializer,
    RouteSerializer,
    RouteStopSerializer,
    ScheduleTemplateSerializer,
    ScheduleSerializer,
    ScheduleSearchSerializer,
    BookingCreateSerializer,
    SearchRouteSerializer,
    BookingCreateSerializer
)
from .services import apply_promo, book_seat
from django.db.models import Count
from django.utils import timezone
from typing import cast, Any


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


class SearchRouteView(APIView):

    def post(self, request):
        serializer = SearchRouteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

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
                status="ACTIVE",
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
            {
                "success": True,
                "results": response_serializer.data,
            },
            status=status.HTTP_200_OK,
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
                id=schedule_id, status="ACTIVE"
            )
        except Schedule.DoesNotExist:
            return Response(
                {"detail": "Schedule not found or inactive"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Validate bus assignment
        try:
            bus_assignment = BusAssignment.objects.select_related(
                "bus"
            ).get(id=bus_assignment_id, schedule=schedule, status="ACTIVE")
        except BusAssignment.DoesNotExist:
            return Response(
                {"detail": "Bus not found for this schedule"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Validate seat number is within bus capacity
        if seat_number < 1 or seat_number > bus_assignment.bus.total_seats:
            return Response(
                {
                    "detail": f"Invalid seat number. This bus has seats 1-{bus_assignment.bus.total_seats}"
                },
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
            },
            status=status.HTTP_201_CREATED,
        )

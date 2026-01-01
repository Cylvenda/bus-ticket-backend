from rest_framework import serializers

from .models import (
    BusAssignment,
    BusCompany,
    Bus,
    Schedule,
    Route,
    Booking,
    RouteStop,
    ScheduleTemplate,
    Passenger,
)


class BusCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = BusCompany
        fields = [
            "id",
            "name",
            "contact_email",
            "contact_phone",
            "license_number",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class BusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bus
        fields = [
            "id",
            "company",
            "plate_number",
            "total_seats",
            "bus_type",
            "amenities",
            "is_active",
        ]
        read_only_fields = ["id"]


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = [
            "id",
            "origin",
            "destination",
            "distance_km",
            "estimated_duration_minutes",
        ]
        read_only_fields = ["id"]

class RouteStopSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouteStop
        fields = [
            "id",
            "route",
            "stop_name",
            "stop_order",
            "arrival_offset_min",
            "departure_offset_min",
        ]
        read_only_fields = ["id"]

class ScheduleTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleTemplate
        fields = [
            "id",
            "route",
            "departure_time",
            "arrival_time",
            "base_price",
            "is_active",
        ]


class ScheduleSerializer(serializers.ModelSerializer):
    route = serializers.CharField(source="template.route.name", read_only=True)
    departure_time = serializers.SerializerMethodField()
    arrival_time = serializers.SerializerMethodField()

    class Meta:
        model = Schedule
        fields = [
            "id",
            "route",
            "departure_time",
            "arrival_time",
            "price",
        ]
        read_only_fields = ["id"]



class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = [
            "id",
            "user",
            "schedule",
            "seat",
            "total_price",
            "booked_at",
            "is_paid",
        ]


class BusAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for individual bus assignments"""

    bus_plate = serializers.CharField(source="bus.plate_number", read_only=True)
    bus_type = serializers.CharField(source="bus.bus_type", read_only=True)
    company_name = serializers.CharField(source="bus.company.name", read_only=True)
    total_seats = serializers.IntegerField(source="bus.total_seats", read_only=True)
    amenities = serializers.CharField(source="bus.amenities", read_only=True)
    available_seats = serializers.SerializerMethodField()

    class Meta:
        model = BusAssignment
        fields = [
            "id",
            "bus_plate",
            "bus_type",
            "company_name",
            "total_seats",
            "amenities",
            "available_seats",
            "status",
        ]

    def get_available_seats(self, obj):
        """Calculate available seats for this specific bus assignment"""
        booked = Booking.objects.filter(
            schedule=obj.schedule,
            # You might need to add a bus field to Booking model
            # or filter by seat numbers assigned to this bus
        ).count()
        return obj.available_seats  # Or: obj.bus.total_seats - booked


class ScheduleSearchSerializer(serializers.ModelSerializer):
    buses = BusAssignmentSerializer(source="bus_assignments", many=True, read_only=True)
    route = serializers.CharField(source="template.route.__str__", read_only=True)
    route_origin = serializers.CharField(source="template.route.origin", read_only=True)
    route_destination = serializers.CharField(
        source="template.route.destination", read_only=True
    )

    class Meta:
        model = Schedule
        fields = [
            "id",
            "route",
            "route_origin",
            "route_destination",
            "travel_date",
            "departure_time",
            "arrival_time",
            "price",
            "buses",  
        ]


class PassengerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Passenger
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "age",
            "gender",
            "nationality",
            "boarding_point",
            "dropping_point",
        ]
        read_only_fields = ["id"]


class BookingCreateSerializer(serializers.Serializer):
    schedule_id = serializers.IntegerField()
    bus_assignment_id = serializers.IntegerField()
    seat_number = serializers.IntegerField(min_value=1)
    promo_code = serializers.CharField(required=False, allow_blank=True, max_length=20)
    passenger = PassengerSerializer()

    def validate_seat_number(self, value):
        if value < 1:
            raise serializers.ValidationError("Seat number must be positive")
        return value


class SearchRouteSerializer(serializers.Serializer):
    origin = serializers.CharField(required=True)
    destination = serializers.CharField(required=True)
    date = serializers.DateField(required=True, input_formats=["%d-%m-%Y"])

    def validate_date(self, value):
        from django.utils import timezone

        if value < timezone.now().date():
            raise serializers.ValidationError("Travel date cannot be in the past.")
        return value

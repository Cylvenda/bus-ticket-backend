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
    SeatLayout,
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

class SeatLayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeatLayout
        fields = ["id", "name", "layout", "total_seats", "is_active"]
        read_only_fields = ["id"]

class BusSerializer(serializers.ModelSerializer):
    total_seats = serializers.IntegerField(source="seat_layout.total_seats", read_only=True)
    seat_layout_structure = serializers.CharField(source="seat_layout.layout", read_only=True)
    class Meta:
        model = Bus
        fields = [
            "id",
            "company",
            "plate_number",
            "bus_type",
            "amenities",
            "is_active",
            "total_seats",
            "seat_layout_structure",
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
    template = ScheduleTemplateSerializer(read_only=True)

    class Meta:
        model = Schedule
        fields = [
            "id",
            "travel_date",
            "departure_time",
            "arrival_time",
            "price",
            "template",
        ]


class BusAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for individual bus assignments"""

    bus_plate = serializers.CharField(source="bus.plate_number", read_only=True)
    bus_type = serializers.CharField(source="bus.bus_type", read_only=True)
    company_name = serializers.CharField(source="bus.company.name", read_only=True)
    amenities = serializers.CharField(source="bus.amenities", read_only=True)
    total_seats = serializers.IntegerField(source="bus.seat_layout.total_seats", read_only=True)
    seat_layout_structure = serializers.JSONField(
        source="bus.seat_layout.layout", read_only=True
    )

    class Meta:
        model = BusAssignment
        fields = [
            "id",
            "bus_plate",
            "bus_type",
            "company_name",
            "amenities",
            "total_seats",
            "available_seats",
            "seat_layout_structure",
        ]


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


class BusMinimalSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = Bus
        fields = ["id", "plate_number", "company_name"]


class BusAssignmentSerializer(serializers.ModelSerializer):
    bus = BusMinimalSerializer(read_only=True)

    class Meta:
        model = BusAssignment
        fields = ["id", "available_seats", "bus"]


class BookingSerializer(serializers.ModelSerializer):
    schedule = ScheduleSerializer(read_only=True)
    bus_assignment = BusAssignmentSerializer(read_only=True)
    passenger = PassengerSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "schedule",
            "bus_assignment",
            "seat_number",
            "price_paid",
            "status",
            "is_paid",
            "booked_at",
            "passenger",
        ]


class SearchRouteSerializer(serializers.Serializer):
    origin = serializers.CharField(required=True)
    destination = serializers.CharField(required=True)
    date = serializers.DateField(required=True, input_formats=["%d-%m-%Y"])

    def validate_date(self, value):
        from django.utils import timezone

        if value < timezone.now().date():
            raise serializers.ValidationError("Travel date cannot be in the past.")
        return value

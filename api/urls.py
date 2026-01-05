from django.urls import path
from .views import (
    SearchRouteView,
    CreateBookingView,
    get_active_routes,
    hold_seat,
    get_seat_status,
)

urlpatterns = [
    path("schedules/search/", SearchRouteView.as_view()),
    path("bookings/", CreateBookingView.as_view()),
    path("routes/active/", get_active_routes, name="active-routes"),
    path("hold-seat/", hold_seat, name="hold-seat"),
    path("get-booked-seats/", get_seat_status, name="get-booked-seats"),
]

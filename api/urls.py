from django.urls import path
from .views import (
    BookingListView,
    SearchRouteView,
    CreateBookingView,
    RouteStopsView,
    UserBookingListView,
    get_active_routes,
    hold_seat,
    get_seat_status,
)

urlpatterns = [
    path("schedules/search/", SearchRouteView.as_view()),
    path("bookings/", CreateBookingView.as_view()),
    path("my-bookings/", UserBookingListView.as_view(), name="user-bookings"),
    path("routes/active/", get_active_routes, name="active-routes"),
    path("hold-seat/", hold_seat, name="hold-seat"),
    path("get-booked-seats/", get_seat_status, name="get-booked-seats"),
    path("get-bookings/", BookingListView.as_view(), name="booking-list"),
    path(
        "route/<int:route_id>/stops/",
        RouteStopsView.as_view(),
        name="schedule-route-stops",
    ),
]

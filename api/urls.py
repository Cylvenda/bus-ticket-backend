from django.urls import path
from .views import SearchRouteView, CreateBookingView

urlpatterns = [
    path("search/", SearchRouteView.as_view()),
    path("bookings/", CreateBookingView.as_view()),
]

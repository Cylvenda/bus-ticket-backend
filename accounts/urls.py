from django.urls import path
from .views import (
    CustomeTokenObtainPairView,
    CustomeTokenRefreshView,
    CustomeTokenVerifyView,
    LogoutView,
)


urlpatterns = [
    path("jwt/create/", CustomeTokenObtainPairView.as_view()),
    path("jwt/refresh/", CustomeTokenRefreshView.as_view()),
    path("jwt/verify/", CustomeTokenVerifyView.as_view()),
    path("logout/", CustomeTokenObtainPairView.as_view()),
]

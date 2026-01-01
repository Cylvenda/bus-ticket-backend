from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from api import views

router = DefaultRouter()
router.register("bus-companies", views.BusCompanyViewSet, basename="bus-company")
router.register("bus", views.BusViewSet, basename="bus")
router.register("route", views.RouteViewSet, basename="route")
router.register("route-stop", views.RouteStopViewSet, basename="route-stop")
router.register(
    "schedule-template", views.ScheduleTemplateViewSet, basename="schedule-template"
)
router.register("schedule", views.ScheduleViewSet, basename="schedule")


schema_view = get_schema_view(
    openapi.Info(
        title="Bus Booking API Doc's",
        default_version="v1.0.0",
        description="This is an API documentation of a Bus Booking System",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # admin site url
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    # Third part urls
    path("api/auth/", include("djoser.urls")),
    path("api/auth/", include("accounts.urls")),
    
    path("api/", include("api.urls")),
    path(
        "swagger<format>/", schema_view.without_ui(cache_timeout=0), name="schema-json"
    ),
    path("", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path(
        "redoc/",
        schema_view.with_ui("redoc", cache_timeout=0),
        name="schema-redoc",
    ),
]

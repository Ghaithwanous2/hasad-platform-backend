"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views.
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


urlpatterns = [
    path("admin/", admin.site.urls),

    path(
        "api/v1/auth/",
        include("accounts.urls"),
    ),

    path(
        "api/v1/operations/",
        include("operations.urls"),
    ),

    path(
        "api/v1/openapi/",
        SpectacularAPIView.as_view(),
        name="schema",
    ),

    path(
        "api/v1/swagger/",
        SpectacularSwaggerView.as_view(
            url_name="schema",
        ),
        name="swagger-ui",
    ),

    path(
        "api/v1/redoc/",
        SpectacularRedocView.as_view(
            url_name="schema",
        ),
        name="redoc",
    ),
]

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CurrentUserView,
    IdentifierTokenObtainPairView,
)


urlpatterns = [
    path(
        "token/",
        IdentifierTokenObtainPairView.as_view(),
        name="token",
    ),
    path(
    "me/",
    CurrentUserView.as_view(),
    name="me",
),
path(
    "token/refresh/",
    TokenRefreshView.as_view(),
    name="token_refresh",
),

]

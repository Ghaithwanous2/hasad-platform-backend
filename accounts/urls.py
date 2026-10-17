from django.urls import path

from .views import IdentifierTokenObtainPairView


urlpatterns = [
    path(
        "token/",
        IdentifierTokenObtainPairView.as_view(),
        name="token",
    ),
]

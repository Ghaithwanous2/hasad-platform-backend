from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CurrentUserView,
    IdentifierTokenObtainPairView,
    RegisterView,
    ResendEmailVerificationView,
    VerifyEmailView,
)





urlpatterns = [
    path(
        "login/",
        IdentifierTokenObtainPairView.as_view(),
        name="login",
    ),
    path(
    "me/",
    CurrentUserView.as_view(),
    name="me",
),
path(
    "refresh/",
    TokenRefreshView.as_view(),
    name="refresh",
),
path(
    "register/",
    RegisterView.as_view(),
    name="register",
),
path(
    "register/verify/",
    VerifyEmailView.as_view(),
    name="verify_email",
),
path(
    "register/resend/",
    ResendEmailVerificationView.as_view(),
    name="resend_email_verification",
),



]

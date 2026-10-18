from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import serializers
from .models import User
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
)


class IdentifierTokenObtainPairSerializer(
    TokenObtainPairSerializer
):
    username_field = "identifier"

    def validate(self, attrs):
        identifier = attrs.get("identifier")
        password = attrs.get("password")

        user = authenticate(
            request=self.context.get("request"),
            identifier=identifier,
            password=password,
        )

        if user is None:
            raise AuthenticationFailed(
                "بيانات تسجيل الدخول غير صحيحة."
            )

        if not user.is_active:
            raise AuthenticationFailed(
                "هذا الحساب غير فعال."
            )

        self.user = user

        refresh = self.get_token(self.user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }







class UserMeSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = (
            "account_id",
            "email",
            "phone",
            "first_name",
            "last_name",
            "full_name",
            "role",
        )

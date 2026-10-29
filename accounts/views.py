
from rest_framework import serializers
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    IdentifierTokenObtainPairSerializer,
    RegisterSerializer,
    ResendEmailVerificationSerializer,
    UserMeSerializer,
    VerifyEmailSerializer,
)

from rest_framework.permissions import AllowAny

from drf_spectacular.utils import extend_schema,inline_serializer


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
    request=RegisterSerializer,
    responses={
        201: inline_serializer(
            name="RegisterResponse",
            fields={
                "message": serializers.CharField(),
                "verification_id": serializers.UUIDField(),
                "account_id": serializers.UUIDField(),
            },
        ),
    },
    tags=["Authentication"],
    summary="Register a farmer or trader",
    description=(
        "Creates a new farmer or trader account "
        "and sends an email verification code."
    ),
)

    def post(self, request):
        serializer = RegisterSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        return Response(
            {
                "message": (
                    "تم إنشاء الحساب. "
                    "تحقق من بريدك الإلكتروني."
                ),
                "verification_id": str(
                    serializer.verification_id,
                ),
                "account_id": str(user.account_id),
            },
            status=status.HTTP_201_CREATED,
        )


class IdentifierTokenObtainPairView(TokenObtainPairView):
    serializer_class = IdentifierTokenObtainPairSerializer



from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response


from .serializers import UserMeSerializer

class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses=UserMeSerializer,
        tags=["Authentication"],
        summary="Get the current authenticated user",
        description=(
            "Returns the profile of the user associated "
            "with the access token."
        ),
    )
    def get(self, request):
        serializer = UserMeSerializer(request.user)
        return Response(serializer.data)


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=VerifyEmailSerializer,
        responses={
            200: inline_serializer(
                name="VerifyEmailResponse",
                fields={
                    "message": serializers.CharField(),
                    "user": UserMeSerializer(),
                    "tokens": inline_serializer(
                        name="AuthenticationTokens",
                        fields={
                            "access": serializers.CharField(),
                            "refresh": serializers.CharField(),
                        },
                    ),
                },
            ),
        },
        tags=["Authentication"],
        summary="Verify email and sign in",
        description=(
            "Verifies the email code, activates the account, "
            "and returns JWT access and refresh tokens."
        ),
    )
    def post(self, request):
        serializer = VerifyEmailSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        result = serializer.save()
        user = result["user"]

        return Response(
            {
                "message": (
                    "تم التحقق من البريد "
                    "وتسجيل الدخول بنجاح."
                ),
                "user": {
                    "account_id": str(user.account_id),
                    "email": user.email,
                    "phone": user.phone,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "full_name": user.full_name,
                    "role": user.role,
                },
                "tokens": {
                    "access": result["access"],
                    "refresh": result["refresh"],
                },
            },
            status=status.HTTP_200_OK,
        )


class ResendEmailVerificationView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=ResendEmailVerificationSerializer,
        responses={
            200: inline_serializer(
                name="ResendEmailVerificationResponse",
                fields={
                    "message": serializers.CharField(),
                },
            ),
        },
        tags=["Authentication"],
        summary="Resend email verification code",
        description=(
            "Sends a new email verification code "
            "to the user's email address."
        ),
    )
    def post(self, request):
        serializer = ResendEmailVerificationSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                "message": (
                    "تم إرسال رمز تحقق جديد "
                    "إلى بريدك الإلكتروني."
                ),
            },
            status=status.HTTP_200_OK,
        )


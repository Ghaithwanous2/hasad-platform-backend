from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import serializers
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
)
from .email_service import send_email_verification_code
from .models import EmailVerification, User
from datetime import timedelta
from .otp import (
    generate_otp_code,
    hash_otp_code,
    verify_otp_code,
)


from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken


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



class RegisterSerializer(serializers.Serializer):
    account_type = serializers.ChoiceField(
        choices=(
            (User.Role.FARMER, "Farmer"),
            (User.Role.TRADER, "Trader"),
        ),
    )

    email = serializers.EmailField()

    phone = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=30,
    )

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )

    password_confirm = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    first_name = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=100,
    )

    last_name = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=100,
    )

    def validate_email(self, value):
        normalized_email = User.objects.normalize_email(value)

        if User.objects.filter(
            email__iexact=normalized_email,
        ).exists():
            raise serializers.ValidationError(
                "لا يمكن استخدام هذا البريد الإلكتروني."
            )

        return normalized_email

    def validate(self, attrs):
        password = attrs["password"]
        password_confirm = attrs["password_confirm"]

        if password != password_confirm:
            raise serializers.ValidationError(
                {
                    "password_confirm": (
                        "كلمتا المرور غير متطابقتين."
                    ),
                }
            )

        validate_password(password)

        return attrs

    @transaction.atomic
    def create(self, validated_data):
                validated_data.pop("password_confirm")

                password = validated_data.pop("password")
                account_type = validated_data.pop("account_type")

                phone = validated_data.pop("phone", None)
                phone = phone.strip() if phone else None

                user = User.objects.create_user(
                    password=password,
                    role=account_type,
                    phone=phone,
                    is_active=False,
                    email_verified=False,
                    phone_verified=False,
                    **validated_data,
                )

                verification_code = generate_otp_code()

                verification = EmailVerification.objects.create(
                    user=user,
                    code_hash=hash_otp_code(verification_code),
                    expires_at=timezone.now() + timedelta(minutes=5),
                )

                send_email_verification_code(
                    recipient_email=user.email,
                    verification_code=verification_code,
                )

                self.verification_id = verification.verification_id

                return user




class VerifyEmailSerializer(serializers.Serializer):
    verification_id = serializers.UUIDField()
    code = serializers.CharField(
        min_length=6,
        max_length=6,
        write_only=True,
    )

    def validate(self, attrs):
        verification_id = attrs["verification_id"]
        code = attrs["code"]

        try:
            verification = EmailVerification.objects.select_related(
                "user",
            ).get(
                verification_id=verification_id,
            )
        except EmailVerification.DoesNotExist:
            raise serializers.ValidationError(
                {
                    "verification_id": (
                        "عملية التحقق غير موجودة."
                    ),
                }
            )

        if verification.verified_at is not None:
            raise serializers.ValidationError(
                "تم استخدام رمز التحقق مسبقاً."
            )

        if verification.expires_at <= timezone.now():
            raise serializers.ValidationError(
                "انتهت صلاحية رمز التحقق."
            )

        if verification.attempts >= 5:
            raise serializers.ValidationError(
                "تم تجاوز عدد المحاولات المسموح."
            )

        if not verify_otp_code(
            code,
            verification.code_hash,
        ):
            verification.attempts += 1
            verification.save(
                update_fields=["attempts"],
            )

            raise serializers.ValidationError(
                "رمز التحقق غير صحيح."
            )

        attrs["verification"] = verification

        return attrs

    def create(self, validated_data):
        verification = validated_data["verification"]
        user = verification.user

        user.is_active = True
        user.email_verified = True
        user.save(
            update_fields=[
                "is_active",
                "email_verified",
                "updated_at",
            ],
        )

        verification.verified_at = timezone.now()
        verification.save(
            update_fields=["verified_at"],
        )

        refresh = RefreshToken.for_user(user)

        return {
            "user": user,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

class ResendEmailVerificationSerializer(serializers.Serializer):
    verification_id = serializers.UUIDField()

    def validate(self, attrs):
        verification_id = attrs["verification_id"]

        try:
            verification = EmailVerification.objects.select_related(
                "user",
            ).get(
                verification_id=verification_id,
            )
        except EmailVerification.DoesNotExist:
            raise serializers.ValidationError(
                {
                    "verification_id": (
                        "عملية التحقق غير موجودة."
                    ),
                }
            )

        if verification.verified_at is not None:
            raise serializers.ValidationError(
                "تم التحقق من البريد مسبقاً."
            )

        if verification.user.is_active:
            raise serializers.ValidationError(
                "هذا الحساب مفعل مسبقاً."
            )

        cooldown = timedelta(seconds=60)
        now = timezone.now()

        if now - verification.last_sent_at < cooldown:
            remaining_seconds = int(
                (
                    cooldown
                    - (now - verification.last_sent_at)
                ).total_seconds()
            )

            raise serializers.ValidationError(
                {
                    "verification_id": (
                        "يرجى الانتظار "
                        f"{remaining_seconds} ثانية قبل إعادة الإرسال."
                    ),
                }
            )

        attrs["verification"] = verification

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        verification = validated_data["verification"]
        verification_code = generate_otp_code()
        now = timezone.now()

        verification.code_hash = hash_otp_code(
            verification_code,
        )
        verification.expires_at = now + timedelta(
            minutes=5,
        )
        verification.attempts = 0
        verification.last_sent_at = now

        verification.save(
            update_fields=[
                "code_hash",
                "expires_at",
                "attempts",
                "last_sent_at",
            ],
        )

        send_email_verification_code(
            recipient_email=verification.user.email,
            verification_code=verification_code,
        )

        return verification

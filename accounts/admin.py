from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("-created_at",)
    list_display = (
        "email",
        "phone",
        "role",
        "is_active",
        "is_staff",
        "created_at",
    )
    list_filter = (
        "role",
        "is_active",
        "is_staff",
        "email_verified",
        "phone_verified",
    )
    search_fields = (
        "email",
        "phone",
        "first_name",
        "last_name",
    )

    fieldsets = (
        (
            "بيانات تسجيل الدخول",
            {
                "fields": (
                    "email",
                    "phone",
                    "password",
                )
            },
        ),
        (
            "المعلومات الشخصية",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "role",
                )
            },
        ),
        (
            "حالة الحساب والصلاحيات",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "التحقق",
            {
                "fields": (
                    "email_verified",
                    "phone_verified",
                )
            },
        ),
        (
            "التواريخ",
            {
                "fields": (
                    "last_login",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    readonly_fields = (
        "last_login",
        "created_at",
        "updated_at",
    )

    add_fieldsets = (
        (
            "إنشاء حساب جديد",
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "phone",
                    "password1",
                    "password2",
                    "role",
                    "is_active",
                    "is_staff",
                ),
            },
        ),
    )

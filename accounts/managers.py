from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """
    مدير إنشاء المستخدمين المخصص لمنصة حصاد.
    """

    def create_user(
        self,
        email=None,
        phone=None,
        password=None,
        **extra_fields,
    ):
        if not email and not phone:
            raise ValueError(
                "يجب إدخال البريد الإلكتروني أو رقم الهاتف."
            )

        if not password:
            raise ValueError(
                "يجب إدخال كلمة المرور."
            )

        if email:
            email = self.normalize_email(email)

        user = self.model(
            email=email,
            phone=phone,
            **extra_fields,
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(
        self,
        email,
        password,
        **extra_fields,
    ):
        if not email:
            raise ValueError(
                "يجب إدخال البريد الإلكتروني للمستخدم الإداري."
            )

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields["role"] = "ADMIN"


        if extra_fields.get("is_staff") is not True:
            raise ValueError(
                "المستخدم الإداري يجب أن يكون is_staff=True."
            )

        if extra_fields.get("is_superuser") is not True:
            raise ValueError(
                "المستخدم الإداري يجب أن يكون is_superuser=True."
            )

        return self.create_user(
            email=email,
            password=password,
            **extra_fields,
        )

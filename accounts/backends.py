from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend


class IdentifierBackend(BaseBackend):
    """
    تسجيل الدخول باستخدام البريد الإلكتروني أو رقم الهاتف.
    """

    def authenticate(
        self,
        request,
        username=None,
        password=None,
        identifier=None,
        **kwargs,
    ):
        login_identifier = identifier or username

        if not login_identifier or not password:
            return None

        User = get_user_model()

        user = None

        if "@" in login_identifier:
            try:
                user = User.objects.get(
                    email__iexact=login_identifier,
                )
            except User.DoesNotExist:
                return None
        else:
            try:
                user = User.objects.get(
                    phone=login_identifier,
                )
            except User.DoesNotExist:
                return None

            allowed_phone_roles = {
                User.Role.FARMER,
                User.Role.TRADER,
            }

            if user.role not in allowed_phone_roles:
                return None

        if not user.check_password(password):
            return None

        if not user.is_active:
            return None

        return user

    def get_user(self, user_id):
        User = get_user_model()

        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

from django.conf import settings
from django.core.mail import send_mail


def send_email_verification_code(
    recipient_email,
    verification_code,
):
    subject = "رمز التحقق لمنصة حصاد"

    message = (
        "مرحباً بك في منصة حصاد.\n\n"
        f"رمز التحقق الخاص بك هو: {verification_code}\n\n"
        "صلاحية الرمز خمس دقائق."
    )

    return send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient_email],
        fail_silently=False,
    )

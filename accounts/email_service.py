import requests

from django.conf import settings


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

    payload = {
        "sender": {
            "email": settings.DEFAULT_FROM_EMAIL,
            "name": "منصة حصاد",
        },
        "to": [
            {
                "email": recipient_email,
            }
        ],
        "subject": subject,
        "textContent": message,
    }

    response = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={
            "accept": "application/json",
            "api-key": settings.BREVO_API_KEY,
            "content-type": "application/json",
        },
        json=payload,
        timeout=15,
    )

    response.raise_for_status()

    return 1

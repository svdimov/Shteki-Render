import requests
from django.conf import settings


def send_brevo_contact_email(*, subject: str, body: str, reply_to: str) -> None:
    """
    Sends contact email via Brevo Transactional Email API.
    Works on Render Free (HTTPS/443), unlike SMTP ports.
    """
    if not settings.BREVO_API_KEY:
        raise RuntimeError("BREVO_API_KEY is not set")

    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": settings.BREVO_API_KEY,
        "content-type": "application/json",
    }

    payload = {
        "sender": {
            # must be a sender/domain you've configured in Brevo, иначе може да откаже
            "name": "Izkriveni Shteki",
            "email": settings.DEFAULT_FROM_EMAIL,
        },
        "to": [{"email": settings.DEFAULT_CONTACT_EMAIL}],
        "subject": subject,
        # Използваме htmlContent, но може и textContent
        "textContent": body,
        "replyTo": {"email": reply_to},
    }

    r = requests.post(url, json=payload, headers=headers, timeout=20)
    r.raise_for_status()
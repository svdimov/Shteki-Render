import requests
from django.conf import settings


def send_brevo_email(
    *,
    to_email: str,
    subject: str,
    text_body: str,
    html_body: str | None = None,
    reply_to: str | None = None,
) -> None:
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
            "name": "Izkriveni Shteki",
            "email": settings.DEFAULT_FROM_EMAIL,
        },
        "to": [{"email": to_email}],
        "subject": subject,
        "textContent": text_body,
    }

    if html_body:
        payload["htmlContent"] = html_body

    if reply_to:
        payload["replyTo"] = {"email": reply_to}

    response = requests.post(url, json=payload, headers=headers, timeout=20)
    response.raise_for_status()


def send_brevo_contact_email(*, subject: str, body: str, reply_to: str) -> None:
    send_brevo_email(
        to_email=settings.DEFAULT_CONTACT_EMAIL,
        subject=subject,
        text_body=body,
        reply_to=reply_to,
    )
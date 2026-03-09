import requests

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from accounts.tokens import account_activation_token


def send_activation_email(request, user):
    protocol = "https" if request.is_secure() else "http"
    domain = request.get_host()

    context = {
        "user": user,
        "domain": domain,
        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
        "token": account_activation_token.make_token(user),
        "protocol": protocol,
    }

    subject = render_to_string(
        "profiles/emails/account_activation_subject.txt",
        context,
    ).strip()

    text_body = render_to_string(
        "profiles/emails/account_activation_email.txt",
        context,
    )

    html_body = render_to_string(
        "profiles/emails/account_activation_email.html",
        context,
    )

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
        "to": [{"email": user.email}],
        "subject": subject,
        "htmlContent": html_body,
        "textContent": text_body,
    }

    response = requests.post(url, json=payload, headers=headers, timeout=20)
    response.raise_for_status()
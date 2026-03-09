from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from accounts.tokens import account_activation_token
from common.brevo_email import send_brevo_email


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

    send_brevo_email(
        to_email=user.email,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
    )


def send_password_reset_email(request, user):
    protocol = "https" if request.is_secure() else "http"
    domain = request.get_host()

    context = {
        "email": user.email,
        "domain": domain,
        "site_name": "Izkriveni Shteki",
        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
        "user": user,
        "token": default_token_generator.make_token(user),
        "protocol": protocol,
    }

    subject = render_to_string(
        "profiles/password_reset_subject.txt",
        context,
    ).strip()

    text_body = render_to_string(
        "profiles/password_reset_email.txt",
        context,
    )

    html_body = render_to_string(
        "profiles/password_reset_email.html",
        context,
    )

    send_brevo_email(
        to_email=user.email,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
    )
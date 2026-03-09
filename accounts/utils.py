from django.conf import settings
from django.core.mail import EmailMultiAlternatives
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

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    email.attach_alternative(html_body, "text/html")
    email.send(fail_silently=False)
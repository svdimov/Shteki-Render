from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        if sociallogin.is_existing:
            return

        email = (
            sociallogin.user.email
            or sociallogin.account.extra_data.get("email")
            or sociallogin.account.user.email
        )

        if not email:
            return

        User = get_user_model()

        try:
            existing_user = User.objects.get(email__iexact=email)
            sociallogin.connect(request, existing_user)
        except User.DoesNotExist:
            pass

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)

        email = (
            data.get("email")
            or sociallogin.account.extra_data.get("email")
            or user.email
        )
        if email:
            user.email = email

        user.is_active = True
        return user
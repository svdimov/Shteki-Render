from django.apps import apps
from django.contrib.auth import get_user_model

from django.contrib.auth.signals import user_login_failed, user_logged_in
from django.db.models.signals import post_save
from django.dispatch import receiver

UserModel = get_user_model()
from accounts.utils import send_password_reset_email

@receiver(post_save, sender=UserModel)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile = apps.get_model("accounts", "Profile")
        Profile.objects.create(user=instance)


@receiver(user_login_failed)
def handle_failed_admin_login(sender, credentials, request, **kwargs):
    if request is None or not request.path.startswith('/admin'):
        return

    email = credentials.get('username')
    try:
        user = UserModel.objects.get(email=email)
        if user.is_locked:
            return

        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 3:
            user.is_locked = True
            user.failed_login_attempts = 0
            user.save(update_fields=['is_locked', 'failed_login_attempts'])

            send_password_reset_email(request, user)
            return

        user.save(update_fields=['failed_login_attempts'])
    except UserModel.DoesNotExist:
        pass

@receiver(user_logged_in)
def reset_failed_attempts(sender, user, request, **kwargs):
    if getattr(user, 'failed_login_attempts', 0):
        user.failed_login_attempts = 0
        user.save()
from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_login_failed, user_logged_in
from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.utils import send_password_reset_email

import logging

logger = logging.getLogger(__name__)

UserModel = get_user_model()


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
    if not email:
        return

    try:
        user = UserModel.objects.get(email=email)

        if user.is_locked:
            return

        user.failed_login_attempts += 1

        if user.failed_login_attempts >= 3:
            user.is_locked = True
            user.failed_login_attempts = 0
            user.save(update_fields=['is_locked', 'failed_login_attempts'])

            try:
                send_password_reset_email(request, user)
            except Exception:
                logger.exception(
                    "Failed to send admin password reset email to %s",
                    user.email,
                )
            return

        user.save(update_fields=['failed_login_attempts'])

    except UserModel.DoesNotExist:
        pass


@receiver(user_logged_in)
def reset_failed_attempts(sender, user, request, **kwargs):
    updates = []

    if getattr(user, 'failed_login_attempts', 0):
        user.failed_login_attempts = 0
        updates.append('failed_login_attempts')

    if getattr(user, 'is_locked', False):
        user.is_locked = False
        updates.append('is_locked')

    if updates:
        user.save(update_fields=updates)
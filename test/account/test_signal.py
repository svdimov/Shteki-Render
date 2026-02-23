from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from accounts.models import Profile
from django.core import mail

UserModel = get_user_model()


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class SignalTest(TestCase):
    def test_profile_created_and_email_sent_on_user_creation(self):
        # Ar
        email = 'testuser@example.com'
        user = UserModel.objects.create_user(email=email, password='Password123!')


        profile = Profile.objects.get(user=user)
        self.assertIsNotNone(profile)


        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Thank you for registering', mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].to, [email])

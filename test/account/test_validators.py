from django.test import override_settings, TestCase
from django.urls import reverse

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class PasswordSpecialCharacterIntegrationTest(TestCase):
    def test_register_password_requires_special_character(self):
        register_url = reverse('register')
        email = 'no.special@example.com'
        password = 'password123'

        response = self.client.post(register_url, {
            'email': email,
            'password1': password,
            'password2': password,
        })

        # Django combines password errors on 'password2' by default.
        errors = response.context['form'].errors.get('password2', [])
        self.assertTrue(any("must contain at least one special character" in e for e in errors))
        self.assertTrue(any("too common" in e for e in errors))

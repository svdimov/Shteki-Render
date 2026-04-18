from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.contrib.auth.tokens import default_token_generator
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import include, path, reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from accounts.forms import (
    AppUserCreationForm,
    CustomAdminAuthenticationForm,
    CustomAuthenticationForm,
    CustomSetPasswordForm,
)
from accounts.models import Profile
from accounts.tokens import account_activation_token
from accounts.validators import FileSizeValidator, SpecialCharacterValidator

UserModel = get_user_model()


def dummy_home_view(request):
    return HttpResponse("home")


urlpatterns = [
    path("", include("accounts.urls")),
    path("home/", dummy_home_view, name="home"),
]


TEST_TEMPLATES = {
    "profiles/register.html": """
{% if form.non_field_errors %}
    {% for error in form.non_field_errors %}
        {{ error }}
    {% endfor %}
{% endif %}
{{ form.as_p }}
""",
    "profiles/login.html": "login",
    "profiles/account-login.html": "account locked",
    "profiles/password_reset.html": "password reset",
    "profiles/password_reset_done.html": "password reset done",
    "profiles/password_reset_confirm.html": "{{ form.as_p }}",
    "profiles/password_reset_complete.html": "password reset complete",
    "profiles/profile-details.html": "{{ profile.user.email }}",
    "profiles/edit-profile.html": "{{ form.as_p }}",
    "profiles/delete-profile.html": "delete profile",
    "profiles/change-password.html": "{{ form.as_p }}",
    "profiles/change-password-done.html": "password change done",
    "profiles/activation-email-sent.html": "activation email sent",
    "profiles/activation-success.html": "activation success {{ activated_user.email }}",
    "profiles/activation-invalid.html": "activation invalid",
    "profiles/emails/account_activation_subject.txt": "Activate account",
    "profiles/emails/account_activation_email.txt": "Activation email for {{ user.email }}",
    "profiles/emails/account_activation_email.html": "<p>Activation email for {{ user.email }}</p>",
    "profiles/password_reset_subject.txt": "Reset password",
    "profiles/password_reset_email.txt": "Reset password email for {{ user.email }}",
    "profiles/password_reset_email.html": "<p>Reset password email for {{ user.email }}</p>",
}


@override_settings(
    ROOT_URLCONF=__name__,
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [],
            "APP_DIRS": False,
            "OPTIONS": {
                "context_processors": [
                    "django.template.context_processors.request",
                    "django.contrib.auth.context_processors.auth",
                ],
                "loaders": [
                    ("django.template.loaders.locmem.Loader", TEST_TEMPLATES),
                ],
            },
        }
    ],
)
class AppUserManagerTests(TestCase):
    def test_create_user_success(self):
        user = UserModel.objects.create_user(
            email="user@example.com",
            password="StrongPass123!",
        )

        self.assertEqual(user.email, "user@example.com")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.check_password("StrongPass123!"))

    def test_create_user_without_email_raises(self):
        with self.assertRaisesMessage(ValueError, "The given email must be set"):
            UserModel.objects.create_user(email=None, password="pass123!@#")

    def test_create_superuser_success(self):
        admin_user = UserModel.objects.create_superuser(
            email="admin@example.com",
            password="AdminPass123!",
        )

        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_active)

    def test_create_superuser_with_invalid_is_staff_raises(self):
        with self.assertRaisesMessage(ValueError, "Superuser must have is_staff=True."):
            UserModel.objects.create_superuser(
                email="admin@example.com",
                password="AdminPass123!",
                is_staff=False,
            )

    def test_create_superuser_with_invalid_is_superuser_raises(self):
        with self.assertRaisesMessage(ValueError, "Superuser must have is_superuser=True."):
            UserModel.objects.create_superuser(
                email="admin@example.com",
                password="AdminPass123!",
                is_superuser=False,
            )


@override_settings(
    ROOT_URLCONF=__name__,
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [],
            "APP_DIRS": False,
            "OPTIONS": {
                "context_processors": [
                    "django.template.context_processors.request",
                    "django.contrib.auth.context_processors.auth",
                ],
                "loaders": [
                    ("django.template.loaders.locmem.Loader", TEST_TEMPLATES),
                ],
            },
        }
    ],
)
class ProfileModelTests(TestCase):
    def setUp(self):
        self.user = UserModel.objects.create_user(
            email="profile@example.com",
            password="StrongPass123!",
        )

    def test_profile_is_created_automatically_via_signal(self):
        self.assertTrue(Profile.objects.filter(user=self.user).exists())

    def test_profile_full_name_property(self):
        profile = self.user.profile
        profile.first_name = "Ivan"
        profile.last_name = "Petrov"

        self.assertEqual(profile.full_name, "Ivan  Petrov")

    def test_profile_picture_or_default_returns_static_path_when_no_picture(self):
        profile = self.user.profile
        self.assertIn("/static/images/2133123", profile.profile_picture_or_default)

    def test_profile_str_with_names(self):
        profile = self.user.profile
        profile.first_name = "Ivan"
        profile.last_name = "Petrov"

        self.assertEqual(str(profile), "Ivan Petrov (profile@example.com)")

    def test_profile_str_without_names(self):
        profile = self.user.profile
        profile.first_name = ""
        profile.last_name = ""

        self.assertEqual(str(profile), "profile@example.com")


@override_settings(
    ROOT_URLCONF=__name__,
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [],
            "APP_DIRS": False,
            "OPTIONS": {
                "context_processors": [
                    "django.template.context_processors.request",
                    "django.contrib.auth.context_processors.auth",
                ],
                "loaders": [
                    ("django.template.loaders.locmem.Loader", TEST_TEMPLATES),
                ],
            },
        }
    ],
)
class ValidatorTests(TestCase):
    def test_file_size_validator_allows_small_file(self):
        validator = FileSizeValidator(max_size_mb=1)
        small_file = SimpleUploadedFile("small.jpg", b"a" * 100)

        validator(small_file)

    def test_file_size_validator_rejects_large_file(self):
        validator = FileSizeValidator(max_size_mb=1)
        large_file = SimpleUploadedFile("large.jpg", b"a" * (1024 * 1024 + 1))

        with self.assertRaisesMessage(Exception, "File size must be under 1 MB"):
            validator(large_file)

    def test_special_character_validator_rejects_password_without_special_char(self):
        validator = SpecialCharacterValidator()

        with self.assertRaisesMessage(Exception, "Password must contain at least one special character."):
            validator.validate("NoSpecial123")

    def test_special_character_validator_accepts_password_with_special_char(self):
        validator = SpecialCharacterValidator()
        validator.validate("HasSpecial123!")


@override_settings(
    ROOT_URLCONF=__name__,
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [],
            "APP_DIRS": False,
            "OPTIONS": {
                "context_processors": [
                    "django.template.context_processors.request",
                    "django.contrib.auth.context_processors.auth",
                ],
                "loaders": [
                    ("django.template.loaders.locmem.Loader", TEST_TEMPLATES),
                ],
            },
        }
    ],
)
class FormTests(TestCase):
    def setUp(self):
        self.user = UserModel.objects.create_user(
            email="locked@example.com",
            password="StrongPass123!",
        )

    def test_app_user_creation_form_has_expected_placeholders(self):
        form = AppUserCreationForm()

        self.assertEqual(form.fields["email"].widget.attrs["placeholder"], "Enter your email")
        self.assertEqual(form.fields["password1"].widget.attrs["placeholder"], "Enter your password")
        self.assertEqual(form.fields["password2"].widget.attrs["placeholder"], "Repeat your password")
        self.assertEqual(form.fields["password1"].help_text, "")
        self.assertEqual(form.fields["password2"].help_text, "")

    def test_custom_authentication_form_blocks_locked_user(self):
        self.user.is_locked = True
        self.user.save(update_fields=["is_locked"])

        form = CustomAuthenticationForm()
        with self.assertRaisesMessage(Exception, "Your account is locked due to too many failed login attempts."):
            form.confirm_login_allowed(self.user)

    def test_custom_admin_authentication_form_blocks_locked_user_in_confirm_login_allowed(self):
        self.user.is_locked = True
        self.user.save(update_fields=["is_locked"])

        form = CustomAdminAuthenticationForm()
        with self.assertRaisesMessage(Exception, "Your account is locked due to too many failed login attempts."):
            form.confirm_login_allowed(self.user)

    def test_custom_set_password_form_removes_help_text(self):
        form = CustomSetPasswordForm(user=self.user)

        self.assertEqual(form.fields["new_password1"].help_text, "")
        self.assertEqual(form.fields["new_password2"].help_text, "")


@override_settings(
    ROOT_URLCONF=__name__,
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [],
            "APP_DIRS": False,
            "OPTIONS": {
                "context_processors": [
                    "django.template.context_processors.request",
                    "django.contrib.auth.context_processors.auth",
                ],
                "loaders": [
                    ("django.template.loaders.locmem.Loader", TEST_TEMPLATES),
                ],
            },
        }
    ],
)
class RegisterViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    @patch("accounts.views.send_activation_email")
    def test_register_view_creates_inactive_user_and_sends_activation_email(self, mocked_send_activation_email):
        response = self.client.post(
            reverse("register"),
            data={
                "email": "newuser@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertRedirects(response, reverse("activation-email-sent"))
        user = UserModel.objects.get(email="newuser@example.com")
        self.assertFalse(user.is_active)
        mocked_send_activation_email.assert_called_once()

    @patch("accounts.views.send_activation_email", side_effect=Exception("mail failure"))
    def test_register_view_rolls_back_user_when_email_send_fails(self, mocked_send_activation_email):
        response = self.client.post(
            reverse("register"),
            data={
                "email": "broken@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(UserModel.objects.filter(email="broken@example.com").exists())
        self.assertContains(response, "Не успяхме да изпратим email за активация. Моля, опитай отново.")
        mocked_send_activation_email.assert_called_once()


@override_settings(
    ROOT_URLCONF=__name__,
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [],
            "APP_DIRS": False,
            "OPTIONS": {
                "context_processors": [
                    "django.template.context_processors.request",
                    "django.contrib.auth.context_processors.auth",
                ],
                "loaders": [
                    ("django.template.loaders.locmem.Loader", TEST_TEMPLATES),
                ],
            },
        }
    ],
)
class ActivationViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UserModel.objects.create_user(
            email="inactive@example.com",
            password="StrongPass123!",
        )
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])

    def test_activation_view_activates_user_with_valid_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = account_activation_token.make_token(self.user)

        response = self.client.get(
            reverse("activate-account", kwargs={"uidb64": uid, "token": token})
        )

        self.user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.user.is_active)
        self.assertContains(response, "activation success")

    def test_activation_view_with_invalid_token_shows_invalid_template(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        response = self.client.get(
            reverse("activate-account", kwargs={"uidb64": uid, "token": "invalid-token"})
        )

        self.user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.user.is_active)
        self.assertContains(response, "activation invalid")


@override_settings(
    ROOT_URLCONF=__name__,
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [],
            "APP_DIRS": False,
            "OPTIONS": {
                "context_processors": [
                    "django.template.context_processors.request",
                    "django.contrib.auth.context_processors.auth",
                ],
                "loaders": [
                    ("django.template.loaders.locmem.Loader", TEST_TEMPLATES),
                ],
            },
        }
    ],
)
class LoginViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UserModel.objects.create_user(
            email="login@example.com",
            password="CorrectPass123!",
        )
        self.user.is_active = True
        self.user.save(update_fields=["is_active"])

    def test_login_success_resets_failed_attempts(self):
        self.user.failed_login_attempts = 2
        self.user.is_locked = False
        self.user.save(update_fields=["failed_login_attempts", "is_locked"])

        response = self.client.post(
            reverse("login"),
            data={"username": "login@example.com", "password": "CorrectPass123!"},
        )

        self.user.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.user.failed_login_attempts, 0)
        self.assertFalse(self.user.is_locked)

    def test_locked_user_cannot_login_even_with_correct_password(self):
        self.user.is_locked = True
        self.user.save(update_fields=["is_locked"])

        response = self.client.post(
            reverse("login"),
            data={"username": "login@example.com", "password": "CorrectPass123!"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.user.is_locked)

    @patch("accounts.views.send_password_reset_email")
    def test_login_three_failed_attempts_locks_user_and_sends_reset_email(self, mocked_send_reset):
        for _ in range(3):
            self.client.post(
                reverse("login"),
                data={"username": "login@example.com", "password": "WrongPass123!"},
            )

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_locked)
        self.assertEqual(self.user.failed_login_attempts, 0)
        mocked_send_reset.assert_called_once()

    def test_locked_user_invalid_login_returns_locked_template(self):
        self.user.is_locked = True
        self.user.save(update_fields=["is_locked"])

        response = self.client.post(
            reverse("login"),
            data={"username": "login@example.com", "password": "WrongPass123!"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "account locked")


@override_settings(
    ROOT_URLCONF=__name__,
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [],
            "APP_DIRS": False,
            "OPTIONS": {
                "context_processors": [
                    "django.template.context_processors.request",
                    "django.contrib.auth.context_processors.auth",
                ],
                "loaders": [
                    ("django.template.loaders.locmem.Loader", TEST_TEMPLATES),
                ],
            },
        }
    ],
)
class PasswordResetConfirmTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UserModel.objects.create_user(
            email="reset@example.com",
            password="OldPass123!",
        )
        self.user.is_active = True
        self.user.is_locked = True
        self.user.failed_login_attempts = 2
        self.user.save(update_fields=["is_active", "is_locked", "failed_login_attempts"])

    def test_password_reset_confirm_unlocks_user_and_resets_failed_attempts(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)

        url = reverse("password_reset_confirm", kwargs={"uidb64": uid, "token": token})

        response = self.client.get(url)
        self.assertIn(response.status_code, (200, 302))

        if response.status_code == 302:
            url = response.url
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

        response = self.client.post(
            url,
            data={
                "new_password1": "BrandNewPass123!",
                "new_password2": "BrandNewPass123!",
            },
        )

        self.user.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.user.is_locked)
        self.assertEqual(self.user.failed_login_attempts, 0)
        self.assertTrue(self.user.check_password("BrandNewPass123!"))


@override_settings(
    ROOT_URLCONF=__name__,
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [],
            "APP_DIRS": False,
            "OPTIONS": {
                "context_processors": [
                    "django.template.context_processors.request",
                    "django.contrib.auth.context_processors.auth",
                ],
                "loaders": [
                    ("django.template.loaders.locmem.Loader", TEST_TEMPLATES),
                ],
            },
        }
    ],
)
class ProfileViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = UserModel.objects.create_user(
            email="user1@example.com",
            password="User1Pass123!",
        )
        self.user2 = UserModel.objects.create_user(
            email="user2@example.com",
            password="User2Pass123!",
        )
        self.user1.is_active = True
        self.user2.is_active = True
        self.user1.save(update_fields=["is_active"])
        self.user2.save(update_fields=["is_active"])

    def test_profile_detail_requires_login(self):
        response = self.client.get(reverse("profile-details", kwargs={"pk": self.user1.pk}))
        self.assertEqual(response.status_code, 302)

    def test_profile_detail_returns_logged_in_user_profile_page(self):
        self.client.force_login(self.user1)

        response = self.client.get(reverse("profile-details", kwargs={"pk": self.user1.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "user1@example.com")

    def test_profile_edit_allows_only_owner(self):
        self.client.force_login(self.user1)

        own_response = self.client.get(reverse("edit-profile", kwargs={"pk": self.user1.pk}))
        other_response = self.client.get(reverse("edit-profile", kwargs={"pk": self.user2.pk}))

        self.assertEqual(own_response.status_code, 200)
        self.assertEqual(other_response.status_code, 403)

    def test_profile_delete_allows_only_owner(self):
        self.client.force_login(self.user1)

        own_response = self.client.get(reverse("delete-profile", kwargs={"pk": self.user1.pk}))
        other_response = self.client.get(reverse("delete-profile", kwargs={"pk": self.user2.pk}))

        self.assertEqual(own_response.status_code, 200)
        self.assertEqual(other_response.status_code, 403)


@override_settings(
    ROOT_URLCONF=__name__,
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [],
            "APP_DIRS": False,
            "OPTIONS": {
                "context_processors": [
                    "django.template.context_processors.request",
                    "django.contrib.auth.context_processors.auth",
                ],
                "loaders": [
                    ("django.template.loaders.locmem.Loader", TEST_TEMPLATES),
                ],
            },
        }
    ],
)
class SignalTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = UserModel.objects.create_user(
            email="adminlock@example.com",
            password="AdminPass123!",
        )
        self.user.is_active = True
        self.user.save(update_fields=["is_active"])

    @patch("accounts.signals.send_password_reset_email")
    def test_admin_failed_login_signal_locks_user_after_three_attempts(self, mocked_send_reset):
        request = self.factory.post("/admin/login/")

        for _ in range(3):
            user_login_failed.send(
                sender=UserModel,
                credentials={"username": "adminlock@example.com"},
                request=request,
            )

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_locked)
        self.assertEqual(self.user.failed_login_attempts, 0)
        mocked_send_reset.assert_called_once()

    def test_non_admin_failed_login_signal_does_not_change_user(self):
        request = self.factory.post("/accounts/login/")

        user_login_failed.send(
            sender=UserModel,
            credentials={"username": "adminlock@example.com"},
            request=request,
        )

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_locked)
        self.assertEqual(self.user.failed_login_attempts, 0)

    def test_user_logged_in_signal_resets_flags(self):
        self.user.is_locked = True
        self.user.failed_login_attempts = 2
        self.user.save(update_fields=["is_locked", "failed_login_attempts"])

        request = self.factory.get("/accounts/login/")
        user_logged_in.send(sender=UserModel, request=request, user=self.user)

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_locked)
        self.assertEqual(self.user.failed_login_attempts, 0)
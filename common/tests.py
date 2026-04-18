from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.forms import BoundField
from django.http import HttpResponse
from django.test import Client, TestCase, override_settings
from django.urls import include, path, reverse

from common.forms import ContactForm
from common.models import EventParticipation
from common.sitemaps import StaticViewSitemap
from common.templatetags.placeholder_filter import placeholder
from events.choices import StatusChoice
from events.models import Event

UserModel = get_user_model()


def dummy_home_view(request):
    return HttpResponse("home")


def dummy_login_view(request):
    return HttpResponse("login")


def dummy_past_events_view(request):
    return HttpResponse("past events")


urlpatterns = [
    path("", include("common.urls")),
    path("accounts/", include("accounts.urls")),
    path("login/", dummy_login_view, name="login"),
    path("home/", dummy_home_view, name="home"),
    path("past-events/", dummy_past_events_view, name="past-events"),
]


TEST_TEMPLATES = {
    "contacts/contacts.html": "{{ form.as_p }}",
    "contacts/contact-success.html": "success",
    "members.html": """
{% for profile in profiles %}
    {{ profile.user.email }}
{% endfor %}
total={{ total_profiles }}
admins={{ administrator_count }}
moderators={{ moderator_count }}
collaborators={{ collaborator_count }}
""",
    "index.html": "home",
}


def create_test_event(**overrides):
    data = {
        "name": "Test Event",
        "start_date": date.today(),
    }
    data.update(overrides)
    return Event.objects.create(**data)


COMMON_OVERRIDE_SETTINGS = override_settings(
    ROOT_URLCONF=__name__,
    LOGIN_URL="/login/",
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


@COMMON_OVERRIDE_SETTINGS
class EventParticipationModelTests(TestCase):
    def setUp(self):
        self.user = UserModel.objects.create_user(
            email="user@test.com",
            password="pass123!@#",
        )
        self.event = create_test_event(name="Test Event")

    def test_create_participation(self):
        participation = EventParticipation.objects.create(
            user=self.user,
            event=self.event,
            status=StatusChoice.WILL_GO,
        )

        self.assertEqual(participation.user, self.user)
        self.assertEqual(participation.event, self.event)
        self.assertEqual(participation.status, StatusChoice.WILL_GO)

    def test_unique_constraint(self):
        EventParticipation.objects.create(
            user=self.user,
            event=self.event,
            status=StatusChoice.WILL_GO,
        )

        with self.assertRaises(IntegrityError):
            EventParticipation.objects.create(
                user=self.user,
                event=self.event,
                status=StatusChoice.MAYBE,
            )

    def test_str(self):
        participation = EventParticipation.objects.create(
            user=self.user,
            event=self.event,
            status=StatusChoice.WILL_GO,
        )

        result = str(participation)
        self.assertIn("Test Event", result)
        self.assertIn("Will go", result)


@COMMON_OVERRIDE_SETTINGS
class EventStatusAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UserModel.objects.create_user(
            email="api@test.com",
            password="pass123!@#",
        )
        self.user.is_active = True
        self.user.save(update_fields=["is_active"])

        self.event = create_test_event(name="API Event")
        self.client.force_login(self.user)

    def test_valid_status_update(self):
        response = self.client.post(
            reverse("api-event-status", kwargs={"pk": self.event.pk}),
            data={"status": StatusChoice.WILL_GO},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Status updated"})
        self.assertTrue(
            EventParticipation.objects.filter(
                user=self.user,
                event=self.event,
                status=StatusChoice.WILL_GO,
            ).exists()
        )

    def test_invalid_status(self):
        response = self.client.post(
            reverse("api-event-status", kwargs={"pk": self.event.pk}),
            data={"status": "INVALID"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "Invalid status"})

    def test_update_existing_status(self):
        EventParticipation.objects.create(
            user=self.user,
            event=self.event,
            status=StatusChoice.MAYBE,
        )

        response = self.client.post(
            reverse("api-event-status", kwargs={"pk": self.event.pk}),
            data={"status": StatusChoice.WILL_GO},
        )

        self.assertEqual(response.status_code, 200)

        participation = EventParticipation.objects.get(
            user=self.user,
            event=self.event,
        )
        self.assertEqual(participation.status, StatusChoice.WILL_GO)

    def test_non_existing_event_returns_404(self):
        response = self.client.post(
            reverse("api-event-status", kwargs={"pk": 999999}),
            data={"status": StatusChoice.WILL_GO},
        )

        self.assertEqual(response.status_code, 404)


@COMMON_OVERRIDE_SETTINGS
class ContactViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    @patch("common.views.send_brevo_contact_email")
    def test_contact_form_valid(self, mocked_send):
        response = self.client.post(
            reverse("contacts"),
            data={
                "name": "Ivan",
                "email": "ivan@test.com",
                "message": "Hello",
            },
        )

        self.assertRedirects(response, reverse("contact-success"))
        mocked_send.assert_called_once_with(
            subject="[Contact] Ivan <ivan@test.com>",
            body="From: Ivan <ivan@test.com>\n\nHello",
            reply_to="ivan@test.com",
        )

    def test_contact_form_invalid(self):
        response = self.client.post(reverse("contacts"), data={})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required", html=False)


class ContactFormTests(TestCase):
    def test_valid_form(self):
        form = ContactForm(
            data={
                "name": "Ivan",
                "email": "ivan@test.com",
                "message": "Hello",
            }
        )
        self.assertTrue(form.is_valid())

    def test_invalid_form(self):
        form = ContactForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)
        self.assertIn("email", form.errors)
        self.assertIn("message", form.errors)

    def test_form_placeholders(self):
        form = ContactForm()
        self.assertEqual(form.fields["name"].widget.attrs["placeholder"], "Enter name")
        self.assertEqual(
            form.fields["email"].widget.attrs["placeholder"],
            "Enter a valid email address",
        )
        self.assertEqual(
            form.fields["message"].widget.attrs["placeholder"],
            "Enter your message",
        )


class PlaceholderFilterTests(TestCase):
    def test_placeholder_filter(self):
        form = ContactForm()
        field = form["name"]

        result = placeholder(field, "Test Placeholder")

        self.assertIsInstance(result, BoundField)
        self.assertEqual(result.field.widget.attrs["placeholder"], "Test Placeholder")


@COMMON_OVERRIDE_SETTINGS
class SitemapTests(TestCase):
    def test_sitemap_items(self):
        sitemap = StaticViewSitemap()
        items = sitemap.items()

        self.assertEqual(items, ["home", "about", "contacts", "past-events"])

    def test_sitemap_location(self):
        sitemap = StaticViewSitemap()

        self.assertEqual(sitemap.location("home"), reverse("home"))
        self.assertEqual(sitemap.location("about"), reverse("about"))

    def test_sitemap_urls(self):
        sitemap = StaticViewSitemap()
        urls = sitemap.get_urls()

        self.assertEqual(len(urls), 8)

        locations = [url["location"] for url in urls]

        self.assertTrue(any(reverse("home") in location for location in locations))
        self.assertTrue(any(reverse("about") in location for location in locations))
        self.assertTrue(any(reverse("contacts") in location for location in locations))


@COMMON_OVERRIDE_SETTINGS
class AboutViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UserModel.objects.create_user(
            email="test@test.com",
            password="pass123!@#",
        )
        self.user.is_active = True
        self.user.save(update_fields=["is_active"])

    def test_about_view_requires_login(self):
        response = self.client.get(reverse("about"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_about_view_logged_user(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("about"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "total=")

    def test_about_view_context_counts(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("about"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_profiles"], 1)
        self.assertEqual(response.context["administrator_count"], 0)
        self.assertEqual(response.context["moderator_count"], 0)
        self.assertEqual(response.context["collaborator_count"], 0)
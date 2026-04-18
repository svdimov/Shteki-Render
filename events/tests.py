from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.test import Client, TestCase, override_settings
from django.urls import include, path, reverse

from common.models import EventParticipation
from events.choices import StatusChoice
from events.forms import CreateEventForm
from events.models import Event, EventLike, EventPost, PostLike
from events.serializers import EventPostSerializer

UserModel = get_user_model()


def dummy_login_view(request):
    return HttpResponse("login")


urlpatterns = [
    path("", include("events.urls")),
    path("accounts/", include("accounts.urls")),
    path("login/", dummy_login_view, name="login"),
]


TEST_TEMPLATES = {
    "events/new-events.html": """
{% for event in new_events %}
    {{ event.name }}
{% endfor %}
""",
    "events/past-event.html": """
{% for event in past_events %}
    {{ event.name }}
{% endfor %}
query={{ query }}
""",
    "events/create-event.html": """
{% if form.errors %}{{ form.errors }}{% endif %}
{{ form.as_p }}
""",
    "events/events-details.html": """
{{ event.name }}
will_go_count={{ will_go_count }}
likes_count={{ likes_count }}
liked_by_me={{ liked_by_me }}
{% for p in participants %}
    {{ p.user.email }}
{% endfor %}
{% for post in event_posts %}
    {{ post.text }}
{% endfor %}
""",
    "events/change-event.html": """
{% if form.errors %}{{ form.errors }}{% endif %}
{{ form.as_p }}
""",
    "events/event-delete.html": "delete event",
}


EVENTS_OVERRIDE_SETTINGS = override_settings(
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


def create_active_user(email="user@example.com", password="Pass123!@#"):
    user = UserModel.objects.create_user(email=email, password=password)
    user.is_active = True
    user.save(update_fields=["is_active"])
    return user


def create_event(**overrides):
    data = {
        "name": "Test Event",
        "location": "Sofia",
        "location_url": "https://example.com/location",
        "description": "Test description",
        "days": 2,
        "status": StatusChoice.WILL_GO,
        "start_date": date.today(),
        "city": "Sofia",
    }
    data.update(overrides)
    return Event.objects.create(**data)


@EVENTS_OVERRIDE_SETTINGS
class EventModelTests(TestCase):
    def test_event_str(self):
        event = create_event(name="Moto Fest")
        self.assertEqual(str(event), "Moto Fest")

    def test_end_date_with_days(self):
        event = create_event(start_date=date(2026, 4, 10), days=3)
        self.assertEqual(event.end_date, date(2026, 4, 13))

    def test_end_date_without_days(self):
        event = create_event(start_date=date(2026, 4, 10), days=None)
        self.assertEqual(event.end_date, date(2026, 4, 10))

    def test_is_past_event_true(self):
        event = create_event(start_date=date.today() - timedelta(days=5), days=1)
        self.assertTrue(event.is_past_event)

    def test_is_past_event_false(self):
        event = create_event(start_date=date.today() + timedelta(days=2), days=1)
        self.assertFalse(event.is_past_event)

    def test_default_image_urls(self):
        event = create_event()
        self.assertEqual(event.image1_url, "/static/images/452545.jpg")
        self.assertEqual(event.image2_url, "/static/images/37.jpg")
        self.assertEqual(event.image3_url, "/static/images/2133123.jpg")


@EVENTS_OVERRIDE_SETTINGS
class EventPostModelTests(TestCase):
    def setUp(self):
        self.user = create_active_user(email="poster@example.com")
        self.event = create_event()

    def test_event_post_str(self):
        post = EventPost.objects.create(
            event=self.event,
            user=self.user,
            text="Hello riders",
        )
        self.assertEqual(str(post), "Hello riders")

    def test_event_post_clean_rejects_empty_text(self):
        post = EventPost(
            event=self.event,
            user=self.user,
            text="   ",
        )

        with self.assertRaisesMessage(ValidationError, "Text cannot be empty."):
            post.clean()

    def test_event_post_clean_accepts_valid_text(self):
        post = EventPost(
            event=self.event,
            user=self.user,
            text="Valid text",
        )
        post.clean()


@EVENTS_OVERRIDE_SETTINGS
class CreateEventFormTests(TestCase):
    def test_form_is_valid_with_required_fields(self):
        form = CreateEventForm(
            data={
                "name": "Event Name",
                "location": "Sofia",
                "location_url": "https://example.com",
                "description": "Description",
                "days": 2,
                "status": StatusChoice.WILL_GO,
                "start_date": "2026-05-10",
                "city": "Sofia",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_placeholders(self):
        form = CreateEventForm()

        self.assertEqual(form.fields["name"].widget.attrs["placeholder"], "Event Name")
        self.assertEqual(form.fields["location"].widget.attrs["placeholder"], "Event Location")
        self.assertEqual(form.fields["location_url"].widget.attrs["placeholder"], "Event Location URL")
        self.assertEqual(form.fields["description"].widget.attrs["placeholder"], "Event Description")
        self.assertEqual(form.fields["days"].widget.attrs["placeholder"], "Event Days")
        self.assertEqual(form.fields["start_date"].widget.attrs["placeholder"], "Start Date")
        self.assertEqual(form.fields["city"].widget.attrs["placeholder"], "Event City")


@EVENTS_OVERRIDE_SETTINGS
class EventPostSerializerTests(TestCase):
    def setUp(self):
        self.user = create_active_user(email="serializer@example.com")
        self.event = create_event()

    def test_serializer_rejects_whitespace_text(self):
        serializer = EventPostSerializer(
            data={
                "event": self.event.pk,
                "text": "   ",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("text", serializer.errors)

    def test_serializer_accepts_valid_text(self):
        serializer = EventPostSerializer(
            data={
                "event": self.event.pk,
                "text": "Nice event",
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)


@EVENTS_OVERRIDE_SETTINGS
class NewAndPastEventViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_active_user(email="viewer@example.com")

        self.future_event = create_event(
            name="Future Event",
            start_date=date.today() + timedelta(days=5),
        )
        self.past_event = create_event(
            name="Past Event",
            start_date=date.today() - timedelta(days=5),
        )

    def test_new_events_requires_login(self):
        response = self.client.get(reverse("new-events"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_new_events_shows_only_future_events(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("new-events"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Future Event")
        self.assertNotContains(response, "Past Event")

    def test_past_events_shows_only_past_events(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("past-events"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Past Event")
        self.assertNotContains(response, "Future Event")

    def test_past_events_search_filters_results(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("past-events"), {"q": "Past"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Past Event")
        self.assertContains(response, "query=Past")


@EVENTS_OVERRIDE_SETTINGS
class CreateEventViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_active_user(email="creator@example.com")
        self.add_permission = Permission.objects.get(codename="add_event")

    def test_create_event_requires_login(self):
        response = self.client.get(reverse("create-event"))
        self.assertEqual(response.status_code, 302)

    def test_create_event_requires_permission(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("create-event"))
        self.assertEqual(response.status_code, 403)

    def test_create_event_success_creates_participation_for_creator(self):
        self.user.user_permissions.add(self.add_permission)
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("create-event"),
            data={
                "name": "Created Event",
                "location": "Plovdiv",
                "location_url": "https://example.com/event",
                "description": "Created from test",
                "days": 1,
                "status": StatusChoice.WILL_GO,
                "start_date": "2026-05-15",
                "city": "Plovdiv",
            },
        )

        self.assertEqual(response.status_code, 302)

        event = Event.objects.get(name="Created Event")
        self.assertEqual(event.creator, self.user)

        self.assertTrue(
            EventParticipation.objects.filter(
                event=event,
                user=self.user,
                status=StatusChoice.WILL_GO,
            ).exists()
        )


@EVENTS_OVERRIDE_SETTINGS
class EventDetailViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_active_user(email="detail@example.com")
        self.other_user = create_active_user(email="other@example.com")
        self.event = create_event(name="Detail Event", creator=self.user)

    def test_event_detail_requires_login(self):
        response = self.client.get(
            reverse("event-details", kwargs={"event_id": self.event.pk})
        )
        self.assertEqual(response.status_code, 302)

    def test_event_detail_context_contains_counts_and_posts(self):
        EventParticipation.objects.create(
            event=self.event,
            user=self.user,
            status=StatusChoice.WILL_GO,
        )
        EventParticipation.objects.create(
            event=self.event,
            user=self.other_user,
            status=StatusChoice.MAYBE,
        )

        EventPost.objects.create(
            event=self.event,
            user=self.user,
            text="First post",
        )
        EventLike.objects.create(
            event=self.event,
            user=self.user,
        )

        self.client.force_login(self.user)
        response = self.client.get(
            reverse("event-details", kwargs={"event_id": self.event.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Detail Event")
        self.assertEqual(response.context["will_go_count"], 1)
        self.assertEqual(response.context["likes_count"], 1)
        self.assertTrue(response.context["liked_by_me"])

    def test_event_detail_post_creates_post_when_text_present(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("event-details", kwargs={"event_id": self.event.pk}),
            data={"text": "New wall post"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            EventPost.objects.filter(
                event=self.event,
                user=self.user,
                text="New wall post",
            ).exists()
        )

    def test_event_detail_post_does_not_create_empty_post(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("event-details", kwargs={"event_id": self.event.pk}),
            data={"text": "   "},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(EventPost.objects.filter(event=self.event).count(), 0)


@EVENTS_OVERRIDE_SETTINGS
class EventPostListCreateAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_active_user(email="postapi@example.com")
        self.event = create_event(name="API Post Event")

    def test_list_posts_returns_posts_for_event(self):
        EventPost.objects.create(event=self.event, user=self.user, text="Post 1")
        EventPost.objects.create(event=self.event, user=self.user, text="Post 2")

        self.client.force_login(self.user)
        response = self.client.get(
            reverse("event-posts", kwargs={"event_id": self.event.pk})
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        if isinstance(data, dict) and "results" in data:
            self.assertEqual(len(data["results"]), 2)
        else:
            self.assertEqual(len(data), 2)

    def test_create_post_requires_authentication(self):
        response = self.client.post(
            reverse("event-posts", kwargs={"event_id": self.event.pk}),
            data={"text": "Unauthorized"},
        )

        self.assertIn(response.status_code, [401, 403])

    def test_create_post_success(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("event-posts", kwargs={"event_id": self.event.pk}),
            data={
                "event": self.event.pk,
                "text": "Created through API",
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            EventPost.objects.filter(
                event=self.event,
                user=self.user,
                text="Created through API",
            ).exists()
        )

    def test_create_post_rejects_empty_text(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("event-posts", kwargs={"event_id": self.event.pk}),
            data={
                "event": self.event.pk,
                "text": "   ",
            },
        )

        self.assertEqual(response.status_code, 400)


@EVENTS_OVERRIDE_SETTINGS
class EventLikeToggleAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_active_user(email="likeevent@example.com")
        self.event = create_event(name="Like Event")

    def test_like_toggle_creates_like(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("event-like", kwargs={"event_id": self.event.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["liked"], True)
        self.assertEqual(response.json()["likes_count"], 1)

    def test_like_toggle_removes_existing_like(self):
        EventLike.objects.create(event=self.event, user=self.user)
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("event-like", kwargs={"event_id": self.event.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["liked"], False)
        self.assertEqual(response.json()["likes_count"], 0)


@EVENTS_OVERRIDE_SETTINGS
class PostLikeToggleAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_active_user(email="likepost@example.com")
        self.event = create_event(name="Post Like Event")
        self.post = EventPost.objects.create(
            event=self.event,
            user=self.user,
            text="Original post",
        )

    def test_post_like_toggle_creates_like(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("post-like", kwargs={"post_id": self.post.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["liked"], True)
        self.assertEqual(response.json()["likes_count"], 1)

    def test_post_like_toggle_removes_existing_like(self):
        PostLike.objects.create(post=self.post, user=self.user)
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("post-like", kwargs={"post_id": self.post.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["liked"], False)
        self.assertEqual(response.json()["likes_count"], 0)


@EVENTS_OVERRIDE_SETTINGS
class EditEventPostAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_active_user(email="editowner@example.com")
        self.other_user = create_active_user(email="editother@example.com")
        self.event = create_event(name="Edit Post Event")
        self.post = EventPost.objects.create(
            event=self.event,
            user=self.user,
            text="Old text",
        )

    def test_edit_post_success_for_owner(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("edit-event-post", kwargs={"post_id": self.post.pk}),
            data={"text": "New text"},
        )

        self.assertEqual(response.status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.text, "New text")

    def test_edit_post_denied_for_non_owner(self):
        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse("edit-event-post", kwargs={"post_id": self.post.pk}),
            data={"text": "Hack text"},
        )

        self.assertEqual(response.status_code, 403)
        self.post.refresh_from_db()
        self.assertEqual(self.post.text, "Old text")

    def test_edit_post_rejects_empty_text(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("edit-event-post", kwargs={"post_id": self.post.pk}),
            data={"text": "   "},
        )

        self.assertEqual(response.status_code, 400)


@EVENTS_OVERRIDE_SETTINGS
class DeleteEventPostAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = create_active_user(email="deleteowner@example.com")
        self.other_user = create_active_user(email="deleteother@example.com")
        self.event = create_event(name="Delete Post Event")
        self.post = EventPost.objects.create(
            event=self.event,
            user=self.owner,
            text="Delete me",
        )
        self.delete_post_permission = Permission.objects.get(codename="delete_eventpost")

    def test_delete_post_success_for_owner(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("delete-event-post", kwargs={"post_id": self.post.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(EventPost.objects.filter(pk=self.post.pk).exists())

    def test_delete_post_denied_for_non_owner_without_permission(self):
        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse("delete-event-post", kwargs={"post_id": self.post.pk})
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(EventPost.objects.filter(pk=self.post.pk).exists())

    def test_delete_post_allowed_for_user_with_permission(self):
        self.other_user.user_permissions.add(self.delete_post_permission)
        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse("delete-event-post", kwargs={"post_id": self.post.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(EventPost.objects.filter(pk=self.post.pk).exists())


@EVENTS_OVERRIDE_SETTINGS
class PastEventsAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_active_user(email="pastevents@example.com")

        self.past_event = create_event(
            name="Old Event",
            location="Varna",
            start_date=date.today() - timedelta(days=10),
        )
        self.future_event = create_event(
            name="Future Event",
            location="Sofia",
            start_date=date.today() + timedelta(days=10),
        )

    def test_past_events_api_requires_authentication(self):
        response = self.client.get(reverse("api-past-events"))
        self.assertIn(response.status_code, [401, 403])

    def test_past_events_api_returns_only_past_events(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("api-past-events"))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["results"][0]["name"], "Old Event")

    def test_past_events_api_search_filters_results(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("api-past-events"), {"q": "Varna"})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["results"][0]["location"], "Varna")


@EVENTS_OVERRIDE_SETTINGS
class AllEventsAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        create_event(name="Alpha Event", location="Sofia")
        create_event(name="Beta Event", location="Varna")

    def test_all_events_api_returns_events(self):
        response = self.client.get(reverse("api-events"))

        self.assertEqual(response.status_code, 200)
        data = response.json()

        if isinstance(data, dict) and "results" in data:
            self.assertEqual(data["count"], 2)
            self.assertEqual(len(data["results"]), 2)
        else:
            self.assertEqual(len(data), 2)

    def test_all_events_api_search_filters_results(self):
        response = self.client.get(reverse("api-events"), {"q": "Varna"})

        self.assertEqual(response.status_code, 200)
        data = response.json()

        if isinstance(data, dict) and "results" in data:
            self.assertEqual(data["count"], 1)
            self.assertEqual(len(data["results"]), 1)
            self.assertEqual(data["results"][0]["name"], "Beta Event")
        else:
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["name"], "Beta Event")


@EVENTS_OVERRIDE_SETTINGS
class EditAndDeleteEventViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = create_active_user(email="eventowner@example.com")
        self.other_user = create_active_user(email="eventother@example.com")
        self.event = create_event(name="Editable Event", creator=self.owner)

        self.change_event_permission = Permission.objects.get(codename="change_event")
        self.delete_event_permission = Permission.objects.get(codename="delete_event")

    def test_edit_event_requires_permission(self):
        self.client.force_login(self.owner)

        response = self.client.get(
            reverse("edit-event", kwargs={"event_id": self.event.pk})
        )

        self.assertEqual(response.status_code, 403)

    def test_edit_event_success(self):
        self.owner.user_permissions.add(self.change_event_permission)
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("edit-event", kwargs={"event_id": self.event.pk}),
            data={
                "name": "Edited Event",
                "location": "Burgas",
                "location_url": "https://example.com/edited",
                "description": "Edited description",
                "days": 4,
                "status": StatusChoice.MAYBE,
                "start_date": "2026-06-01",
                "city": "Burgas",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.event.refresh_from_db()
        self.assertEqual(self.event.name, "Edited Event")
        self.assertEqual(self.event.city, "Burgas")
        self.assertEqual(self.event.status, StatusChoice.MAYBE)

    def test_delete_event_requires_permission(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("delete-event", kwargs={"event_id": self.event.pk})
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Event.objects.filter(pk=self.event.pk).exists())

    def test_delete_event_success(self):
        self.owner.user_permissions.add(self.delete_event_permission)
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("delete-event", kwargs={"event_id": self.event.pk})
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Event.objects.filter(pk=self.event.pk).exists())
from django.test import TestCase

# Create your tests here.
from datetime import date
from io import BytesIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.test import Client, TestCase, override_settings
from django.urls import include, path, reverse

from events.choices import StatusChoice
from events.models import Event
from photos.forms import PhotoUploadForm
from photos.models import Photo

UserModel = get_user_model()


def dummy_login_view(request):
    return HttpResponse("login")


urlpatterns = [
    path("", include("photos.urls")),
    path("login/", dummy_login_view, name="login"),
]


TEST_TEMPLATES = {
    "photos/photos.html": """
{% for event in events %}
    {{ event.name }}
{% endfor %}
""",
    "photos/photos-detail.html": """
{% if form_error %}{{ form_error }}{% endif %}
{% if event %}{{ event.name }}{% endif %}
{% if photo %}{{ photo.id }}{% endif %}
{% for p in photos %}
    {{ p.id }}
{% endfor %}
{{ form.as_p }}
""",
    "photos/photos-delete.html": """
delete photo {{ object.id }}
{% if event %}{{ event.name }}{% endif %}
""",
}


PHOTOS_OVERRIDE_SETTINGS = override_settings(
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


def make_test_image(name="test.gif", size=43):
    # Valid 1x1 GIF
    gif_bytes = (
        b"GIF89a\x01\x00\x01\x00\x80\x00\x00"
        b"\x00\x00\x00\xff\xff\xff!"
        b"\xf9\x04\x01\x00\x00\x00\x00,"
        b"\x00\x00\x00\x00\x01\x00\x01\x00"
        b"\x00\x02\x02D\x01\x00;"
    )
    if size > len(gif_bytes):
        gif_bytes = gif_bytes + (b"a" * (size - len(gif_bytes)))
    return SimpleUploadedFile(name, gif_bytes, content_type="image/gif")


@PHOTOS_OVERRIDE_SETTINGS
class PhotoModelTests(TestCase):
    def setUp(self):
        self.user = create_active_user(email="photo-model@example.com")
        self.event = create_event(name="Photo Event")

    def test_photo_str(self):
        photo = Photo.objects.create(
            event=self.event,
            user=self.user,
            image=make_test_image(),
        )

        self.assertIn("Photo by", str(photo))
        self.assertIn(self.event.name, str(photo))

    def test_photo_is_created(self):
        photo = Photo.objects.create(
            event=self.event,
            user=self.user,
            image=make_test_image(),
        )

        self.assertEqual(photo.event, self.event)
        self.assertEqual(photo.user, self.user)
        self.assertTrue(bool(photo.image))


class PhotoUploadFormTests(TestCase):
    def test_form_valid(self):
        form = PhotoUploadForm(
            files={"image": make_test_image()}
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_invalid_without_image(self):
        form = PhotoUploadForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("image", form.errors)


@PHOTOS_OVERRIDE_SETTINGS
class PhotosViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_active_user(email="photos-view@example.com")
        self.event1 = create_event(name="Event 1")
        self.event2 = create_event(name="Event 2")

    def test_photos_view_requires_login(self):
        response = self.client.get(reverse("photos"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_photos_view_lists_events(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("photos"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Event 1")
        self.assertContains(response, "Event 2")


@PHOTOS_OVERRIDE_SETTINGS
class PhotoAddViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_active_user(email="photo-add@example.com")
        self.event = create_event(name="Upload Event")

    def test_photo_add_requires_login(self):
        response = self.client.get(
            reverse("photos-detail", kwargs={"event_id": self.event.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_photo_add_get_returns_page(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("photos-detail", kwargs={"event_id": self.event.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Upload Event")

    def test_photo_upload_no_image_shows_error(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("photos-detail", kwargs={"event_id": self.event.pk}),
            data={},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You must select at least one image.")
        self.assertEqual(Photo.objects.count(), 0)

    def test_photo_upload_valid(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("photos-detail", kwargs={"event_id": self.event.pk}),
            data={"images": make_test_image("valid.gif")},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Photo.objects.count(), 1)

        photo = Photo.objects.get()
        self.assertEqual(photo.user, self.user)
        self.assertEqual(photo.event, self.event)

    def test_photo_upload_multiple_valid_images(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("photos-detail", kwargs={"event_id": self.event.pk}),
            data={
                "images": [
                    make_test_image("one.gif"),
                    make_test_image("two.gif"),
                ]
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Photo.objects.count(), 2)

    def test_photo_upload_invalid_extension_shows_error(self):
        self.client.force_login(self.user)

        bad_file = SimpleUploadedFile(
            "bad.txt",
            b"not-an-image",
            content_type="text/plain",
        )

        response = self.client.post(
            reverse("photos-detail", kwargs={"event_id": self.event.pk}),
            data={"images": bad_file},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Photo.objects.count(), 0)

    def test_photo_upload_too_large_file_shows_error(self):
        self.client.force_login(self.user)

        too_large = make_test_image(size=(9 * 1024 * 1024) + 1)

        response = self.client.post(
            reverse("photos-detail", kwargs={"event_id": self.event.pk}),
            data={"images": too_large},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Photo.objects.count(), 0)
        self.assertContains(response, "File size must be under 9 MB", html=False)


@PHOTOS_OVERRIDE_SETTINGS
class PhotoDetailViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_active_user(email="photo-detail@example.com")
        self.event = create_event(name="Detail Event")
        self.photo = Photo.objects.create(
            event=self.event,
            user=self.user,
            image=make_test_image(),
        )

    def test_photo_detail_requires_login(self):
        response = self.client.get(
            reverse("photo-detail", kwargs={"pk": self.photo.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_photo_detail_view_for_logged_user(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("photo-detail", kwargs={"pk": self.photo.pk})
        )

        # PermissionRequiredMixin has no permission_required in your code,
        # but for many setups this still renders the detail page.
        # If it later breaks, this is the place to adjust.
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(self.photo.pk))


@PHOTOS_OVERRIDE_SETTINGS
class PhotoDeleteViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = create_active_user(email="photo-owner@example.com")
        self.other_user = create_active_user(email="photo-other@example.com")
        self.event = create_event(name="Delete Event")
        self.photo = Photo.objects.create(
            event=self.event,
            user=self.owner,
            image=make_test_image(),
        )
        self.delete_permission = Permission.objects.get(codename="delete_photo")

    def test_photo_delete_requires_login(self):
        response = self.client.post(
            reverse("photo-delete", kwargs={"pk": self.photo.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Photo.objects.filter(pk=self.photo.pk).exists())

    def test_photo_delete_allowed_for_owner(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("photo-delete", kwargs={"pk": self.photo.pk})
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Photo.objects.filter(pk=self.photo.pk).exists())

    def test_photo_delete_denied_for_non_owner_without_permission(self):
        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse("photo-delete", kwargs={"pk": self.photo.pk})
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Photo.objects.filter(pk=self.photo.pk).exists())

    def test_photo_delete_allowed_for_user_with_permission(self):
        self.other_user.user_permissions.add(self.delete_permission)
        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse("photo-delete", kwargs={"pk": self.photo.pk})
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Photo.objects.filter(pk=self.photo.pk).exists())

    def test_photo_delete_respects_next_parameter(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("photo-delete", kwargs={"pk": self.photo.pk}),
            data={"next": "/custom-next/"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/custom-next/")
        self.assertFalse(Photo.objects.filter(pk=self.photo.pk).exists())
from urllib import response

from django.conf import urls
from django.test import TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from events.models import Event
from photos.models import Photo
from events.choices import StatusChoice
from django.utils import timezone


UserModel = get_user_model()


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class TestPhotoAddView(TestCase):
    def setUp(self):
        self.user = UserModel.objects.create_user(email='user@example.com', password='testpass123')
        self.client.login(email='user@example.com', password='testpass123')
        self.event = Event.objects.create(
            name='Test Event',
            location='Test Location',
            city='Test City',
            start_date=timezone.now().date(),
            status=StatusChoice.WILL_GO,
            creator=self.user,
        )

    def test_photo_upload_valid(self):
        url = reverse('photos-detail', kwargs={'event_id': self.event.pk})
        image = SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")

        response = self.client.post(
            url,
            data={},
            files={'images': image},
            follow=True
        )

        print("Form error:", response.context.get('form_error'))
        print("Photos:", Photo.objects.all())
        self.assertEqual(Photo.objects.filter(event=self.event, user=self.user).count(), 1)
        self.assertRedirects(response, url)

    def test_photo_upload_no_image_shows_error(self):
        url = reverse('photos-detail', kwargs={'event_id': self.event.pk})

        response = self.client.post(url, {}, follow=True)

        # Should NOT create a photo, should render error in response
        self.assertEqual(Photo.objects.filter(event=self.event, user=self.user).count(), 0)
        self.assertContains(response, "You must select at least one image.")

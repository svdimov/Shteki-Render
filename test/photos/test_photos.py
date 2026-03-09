

from django.conf import urls
from django.test import TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from events.models import Event
from photos.models import Photo
from events.choices import StatusChoice
from django.utils import timezone

from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile


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



    def get_test_image(self):
        file_obj = BytesIO()
        image = Image.new("RGB", (100, 100))
        image.save(file_obj, format="JPEG")
        file_obj.seek(0)
        return SimpleUploadedFile(
            "test.jpg",
            file_obj.read(),
            content_type="image/jpeg"
        )

    def test_photo_upload_valid(self):
        url = reverse('photos-detail', kwargs={'event_id': self.event.pk})
        image = self.get_test_image()

        response = self.client.post(
            url,
            data={'images': image},
            follow=True
        )

        self.assertEqual(
            Photo.objects.filter(event=self.event, user=self.user).count(),
            1
        )

    def test_photo_upload_no_image_shows_error(self):
        url = reverse('photos-detail', kwargs={'event_id': self.event.pk})

        response = self.client.post(url, {}, follow=True)

        # Should NOT create a photo, should render error in response
        self.assertEqual(Photo.objects.filter(event=self.event, user=self.user).count(), 0)
        self.assertContains(response, "You must select at least one image.")

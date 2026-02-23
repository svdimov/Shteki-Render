from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

from django.db import models
from django.utils import timezone
from datetime import timedelta

from django.contrib.auth import get_user_model

from accounts.validators import FileSizeValidator
from events.choices import StatusChoice


class Event(models.Model):
    name = models.CharField(max_length=255)

    location = models.CharField(max_length=255)

    location_url = models.URLField(blank=True, null=True)

    description = models.TextField(blank=True, null=True)

    days = models.PositiveIntegerField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=StatusChoice,

    )
    start_date = models.DateField()

    city = models.CharField(max_length=100)

    image1 = models.ImageField(
        upload_to='event_images/',
        blank=True,

        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif']),
            FileSizeValidator(max_size_mb=6)
        ]
    )
    image2 = models.ImageField(
        upload_to='event_images/',
        blank=True,

        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif']),
            FileSizeValidator(max_size_mb=6)
        ]
    )
    image3 = models.ImageField(
        upload_to='event_images/',
        blank=True,

        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif']),
            FileSizeValidator(max_size_mb=6)
        ]
    )

    created_at = models.DateTimeField(auto_now_add=True)

    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # не се изтрива събитието, ако потребителят е изтрит не е чата
        related_name='created_events',
        blank=True,
        null=True
    )

    @property
    def image1_url(self):
        if self.image1 and hasattr(self.image1, 'url'):
            return self.image1.url

        return '/static/images/452545.jpg'

    @property
    def image2_url(self):
        if self.image2 and hasattr(self.image2, 'url'):
            return self.image2.url

        return '/static/images/37.jpg'

    @property
    def image3_url(self):
        if self.image3 and hasattr(self.image3, 'url'):
            return self.image3.url

        return '/static/images/2133123.jpg'

    def __str__(self):
        return self.name

    @property
    def end_date(self):

        if self.days:
            return self.start_date + timedelta(days=self.days)
        return self.start_date

    @property
    def is_past_event(self):

        return self.end_date < timezone.now().date()


User = get_user_model()


class EventPost(models.Model):
    event = models.ForeignKey('Event', on_delete=models.CASCADE, related_name='posts')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(
        max_length=100,
        error_messages={
            'max_length': 'Text cannot be more than 300 characters.'
        })
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if not self.text or not self.text.strip():
            raise ValidationError("Text cannot be empty.")

    def __str__(self):
        return self.text


class EventLike(models.Model):
    event = models.ForeignKey('Event', on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event', 'user')



class PostLike(models.Model):
    post = models.ForeignKey(EventPost, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')

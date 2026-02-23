from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
from events.models import Event  # reference your Event model
from django.core.validators import FileExtensionValidator
from accounts.validators import FileSizeValidator

class Photo(models.Model):
    event = models.ForeignKey(Event, related_name='user_photos', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    image = models.ImageField(
        upload_to='user_event_photos/',
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif']),
            FileSizeValidator(max_size_mb=9),
        ]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Photo by {self.user} for {self.event.name}'

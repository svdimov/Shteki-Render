from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
from events.models import Event
from events.choices import StatusChoice

class EventParticipation(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='event_participations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_participations')
    status = models.CharField(max_length=20, choices=StatusChoice.choices)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event', 'user')

    def __str__(self):
        return f'{self.user} - {self.event} - {self.status}'

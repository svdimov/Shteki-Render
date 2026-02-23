from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from common.models import EventParticipation
from events.models import Event
from events.choices import StatusChoice

User = get_user_model()

class EventParticipationModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='janedoe@example.com', password='testpass123')
        self.event = Event.objects.create(
            name="Music Fest",
            start_date=timezone.now()

        )

    def test_create_participation(self):
        participation = EventParticipation.objects.create(
            event=self.event,
            user=self.user,
            status=StatusChoice.WILL_GO
        )
        self.assertEqual(participation.status, StatusChoice.WILL_GO)
        self.assertIn(self.user.email, str(participation))
        self.assertIn(str(self.event), str(participation))
        self.assertIn(StatusChoice.WILL_GO, str(participation))

    def test_unique_together_constraint(self):
        EventParticipation.objects.create(
            event=self.event,
            user=self.user,
            status=StatusChoice.MAYBE
        )
        from django.db.utils import IntegrityError
        with self.assertRaises(IntegrityError):
            EventParticipation.objects.create(
                event=self.event,
                user=self.user,
                status=StatusChoice.NOT_GOING
            )

    def test_created_at_autoset(self):
        participation = EventParticipation.objects.create(
            event=self.event,
            user=self.user,
            status=StatusChoice.NOT_GOING
        )
        self.assertIsNotNone(participation.created_at)

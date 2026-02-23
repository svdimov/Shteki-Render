
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from events.models import Event
from events.choices import StatusChoice

class EventModelLogicTests(TestCase):
    def setUp(self):
        self.base_data = {
            'name': 'Scenario Event',
            'location': 'Scenario Location',
            'status': StatusChoice.WILL_GO,
            'city': 'Scenario City',
        }

    def test_end_date_with_positive_days(self):
        start_date = timezone.now().date()
        event = Event.objects.create(
            **self.base_data,
            start_date=start_date,
            days=2,
        )
        self.assertEqual(event.end_date, start_date + timedelta(days=2))

    def test_end_date_with_zero_days(self):
        start_date = timezone.now().date()
        event = Event.objects.create(
            **self.base_data,
            start_date=start_date,
            days=0,
        )
        self.assertEqual(event.end_date, start_date)

    def test_is_past_event_true(self):
        start_date = timezone.now().date() - timedelta(days=5)
        event = Event.objects.create(
            **self.base_data,
            start_date=start_date,
            days=1,
        )
        self.assertTrue(event.is_past_event)

    def test_is_past_event_false(self):
        start_date = timezone.now().date() + timedelta(days=2)
        event = Event.objects.create(
            **self.base_data,
            start_date=start_date,
            days=2,
        )
        self.assertFalse(event.is_past_event)
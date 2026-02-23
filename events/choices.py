from django.db import models


class StatusChoice(models.TextChoices):

    WILL_GO = 'Will go', 'Will go'
    MAYBE = 'Maybe', 'Maybe'
    NOT_GOING = 'Not going', 'Not going'

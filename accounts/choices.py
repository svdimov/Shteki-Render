from django.db import models

class GenderChoice(models.TextChoices):
    MALE = 'Male', 'Male'
    FEMALE = 'Female', 'Female'
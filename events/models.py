from django.db import models
from django.utils import timezone


class Event(models.Model):
    TYPE_CHOICES = [
        ('formation', 'Formation'),
        ('conference', 'Conférence'),
        ('atelier', 'Atelier'),
        # ... autres types
    ]
    LOCATION_CHOICES = [
        ('digital', 'Digital'),
        ('fablab', 'Fab Lab'),
        # ... autres lieux
    ]

    title = models.CharField(max_length=200)
    event_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    location = models.CharField(max_length=50, choices=LOCATION_CHOICES)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(blank=True, null=True)
    description = models.TextField(blank=True)

    # ... autres champs nécessaires

    def _str_(self):
        return self.title
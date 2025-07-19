from django.db import models
from django.conf import settings
from events.models import Event

class Attendance(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    present = models.BooleanField(default=False)

    def _str_(self):
        return f"{self.user.username} - {self.event.title} - {self.date}"
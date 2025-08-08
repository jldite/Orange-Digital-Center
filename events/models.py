import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify


class Event(models.Model):
    EVENT_TYPES = (
        ('FORMATION', 'Formation'),
        ('CONFERENCE', 'Conférence'),
        ('ATELIER', 'Atelier'),
        ('TALK', 'Talk'),
        ('OPEN_LAB', 'Open Lab'),
        ('MASTER_CLASS', 'Master Class'),
        ('SUPER_CODEURS', 'Super Codeurs'),
        ('MAKER_JUNIOR', 'Maker Junior'),
    )

    LOCATIONS = (
        ('DIGITAL', 'Digital'),
        ('FAB_LAB', 'Fab Lab'),
        ('ODC_CLUB', 'ODC Club'),
        ('ONLINE', 'En ligne'),
    )

    TAGS = (
        ('FEMME', 'Femmes'),
        ('ETUDIANT', 'Étudiants'),
        ('JEUNE', 'Jeunes'),
        ('ENTREPRENEUR', 'Entrepreneurs'),
        ('STARTUP', 'Startups'),
        ('PROFESSIONNEL', 'Professionnels'),
    )
    cover_image = models.ImageField(
        upload_to='event_cover_images/',
        blank=True,
        null=True,
        verbose_name="Image de couverture",
        help_text="Image représentative de l'événement (format: JPG, PNG)"
    )

    qr_code = models.FileField(
        upload_to='event_qr_codes/',
        blank=True,
        null=True,
        verbose_name="QR Code"
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField()
    type = models.CharField(max_length=50, choices=EVENT_TYPES)
    location = models.CharField(max_length=50, choices=LOCATIONS)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    capacity = models.PositiveIntegerField( default=30,
        validators=[MinValueValidator(1)],
        verbose_name="Capacité maximale")
    image = models.ImageField(upload_to='event_images/', blank=True, null=True)
    qr_code = models.ImageField(upload_to='event_qr_codes/', blank=True, null=True)
    tags = models.CharField(max_length=100, choices=TAGS, blank=True)
    instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Registration(models.Model):
    event = models.ForeignKey('Event', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    registration_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'En attente'),
            ('CONFIRMED', 'Confirmé'),
            ('CANCELED', 'Annulé'),
        ],
        default='PENDING'
    )

    class Meta:
        unique_together = ('event', 'user')
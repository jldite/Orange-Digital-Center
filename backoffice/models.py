from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
import qrcode
from io import BytesIO
from django.core.files import File
from django.core.files.base import ContentFile
import os

try:
    from taggit.managers import TaggableManager
except ImportError:
    # Fallback si taggit n'est pas installé
    class TaggableManager:
        def __init__(self, *args, **kwargs):
            pass


class CustomUser(AbstractUser):
    GENDER_CHOICES = [
        ('M', 'Homme'),
        ('F', 'Femme'),
        ('O', 'Autre'),
        ('P', 'Préfère ne pas dire'),
    ]

    ROLE_CHOICES = [
        ('ADMIN', 'Administrateur'),
        ('STAFF', 'Personnel ODC'),
        ('TRAINER', 'Formateur'),
        ('PARTICIPANT', 'Participant'),
    ]

    # Champs supplémentaires
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        blank=True,
        null=True,
        verbose_name="Genre"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Téléphone"
    )
    birth_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date de naissance"
    )
    organization = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Organisation/Établissement"
    )
    university = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Université"
    )
    qr_code = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="QR Code"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='PARTICIPANT',
        verbose_name="Rôle"
    )
    photo = models.ImageField(
        upload_to='user_photos/',
        blank=True,
        null=True,
        verbose_name="Photo de profil"
    )
    tags = TaggableManager(blank=True, verbose_name="Tags")

    # Champs de suivi
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    def get_absolute_url(self):
        return reverse('backoffice:user_detail', kwargs={'user_id': self.id})

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        if self.birth_date:
            today = timezone.now().date()
            return today.year - self.birth_date.year - (
                    (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
            )
        return None


class Event(models.Model):
    TYPE_CHOICES = [
        ('FORMATION', 'Formation'),
        ('CONF', 'Conférence'),
        ('TALK', 'Talk'),
        ('OPENLAB', 'Open lab'),
        ('FABCAFE', 'Fab café'),
        ('MASTERCLASS', 'Master class'),
        ('ATELIER', 'Atelier'),
        ('SUPERCODEURS', 'Super codeurs'),
        ('MAKERJUNIOR', 'Maker junior'),
    ]

    LOCATION_CHOICES = [
        ('DIGITAL', 'Digital'),
        ('FABLAB', 'Fab lab'),
        ('FAB', 'Fab'),
        ('ODCCLUBS', 'ODC clubs'),
    ]

    STATUS_CHOICES = [
        ('UPCOMING', 'À venir'),
        ('ONGOING', 'En cours'),
        ('COMPLETED', 'Terminé'),
        ('CANCELED', 'Annulé'),
    ]

    # Informations de base
    title = models.CharField(max_length=200, verbose_name="Titre")
    description = models.TextField(verbose_name="Description")
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='FORMATION',
        verbose_name="Type d'événement"
    )
    location = models.CharField(
        max_length=20,
        choices=LOCATION_CHOICES,
        default='DIGITAL',
        verbose_name="Lieu"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='UPCOMING',
        verbose_name="Statut"
    )

    # Dates et heures
    start_date = models.DateTimeField(verbose_name="Date et heure de début")
    end_date = models.DateTimeField(verbose_name="Date et heure de fin")
    registration_deadline = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Date limite d'inscription"
    )

    # Capacité et inscription
    capacity = models.PositiveIntegerField(
        default=30,
        validators=[MinValueValidator(1)],
        verbose_name="Capacité maximale"
    )
    is_published = models.BooleanField(default=False, verbose_name="Publié")
    requires_approval = models.BooleanField(default=True, verbose_name="Nécessite approbation")

    # Relations
    organizer = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        related_name='organized_events',
        null=True,
        blank=True,
        verbose_name="Organisateur"
    )
    tags = TaggableManager(blank=True, verbose_name="Tags")

    # Suivi
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Événement"
        verbose_name_plural = "Événements"
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['start_date']),
            models.Index(fields=['status']),
            models.Index(fields=['type']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_type_display()}) - {self.start_date.strftime('%d/%m/%Y')}"

    def get_absolute_url(self):
        return reverse('backoffice:event_detail', kwargs={'event_id': self.id})

    def save(self, *args, **kwargs):
        # Mise à jour automatique du statut en fonction des dates
        now = timezone.now()
        if self.start_date > now:
            self.status = 'UPCOMING'
        elif self.start_date <= now <= self.end_date:
            self.status = 'ONGOING'
        elif now > self.end_date:
            self.status = 'COMPLETED'

        super().save(*args, **kwargs)

    @property
    def duration(self):
        return self.end_date - self.start_date

    @property
    def is_full(self):
        return self.applications.approved().count() >= self.capacity

    @property
    def available_seats(self):
        return max(0, self.capacity - self.applications.approved().count())

    def generate_qr_code(self):
        if not self.id:
            self.save()

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        # L'URL pourrait pointer vers une page de confirmation de présence
        url = f"https://odc.example.com/events/{self.id}/checkin/"
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Sauvegarder l'image dans un BytesIO
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        # Créer un nom de fichier unique
        filename = f"event_{self.id}_qr.png"

        # Sauvegarder dans le champ qr_code
        self.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)
        buffer.close()

    @property
    def participants_count(self):
        return self.applications.approved().count()

    @property
    def attendance_rate(self):
        total_present = sum(app.attendance.filter(present=True).count() for app in self.applications.all())
        total_sessions = self.attendance_dates.count()

        if total_sessions > 0 and self.participants_count > 0:
            return (total_present / (total_sessions * self.participants_count)) * 100
        return 0


class Application(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('APPROVED', 'Approuvé'),
        ('REJECTED', 'Rejeté'),
        ('WAITLISTED', 'Liste d\'attente'),
        ('CANCELLED', 'Annulé'),
    ]
    #champ pour la référence frontoffice
    frontoffice_registration_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="ID Inscription Frontoffice"
    )

    # Relations
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name="Événement"
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name="Participant"
    )

    # Statut et suivi
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="Statut de l'inscription"
    )
    applied_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'inscription")
    approved_at = models.DateTimeField(blank=True, null=True, verbose_name="Date d'approbation")
    rejection_reason = models.TextField(blank=True, null=True, verbose_name="Raison du rejet")

    # Informations supplémentaires
    motivation = models.TextField(blank=True, null=True, verbose_name="Motivation")
    expectations = models.TextField(blank=True, null=True, verbose_name="Attentes")

    class Meta:
        verbose_name = "Inscription"
        verbose_name_plural = "Inscriptions"
        unique_together = ('event', 'user')
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.user} - {self.event} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        # Enregistrer la date d'approbation si le statut passe à APPROVED
        if self.status == 'APPROVED' and not self.approved_at:
            self.approved_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def attendance_rate(self):
        total_sessions = self.event.attendance_dates.count()
        attended_sessions = self.attendance.filter(present=True).count()

        if total_sessions > 0:
            return (attended_sessions / total_sessions) * 100
        return 0


class Attendance(models.Model):
    # Relations
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='attendance',
        verbose_name="Inscription"
    )

    # Date et présence
    date = models.DateField(verbose_name="Date")
    present = models.BooleanField(default=False, verbose_name="Présent")

    # Horaires
    check_in = models.DateTimeField(blank=True, null=True, verbose_name="Heure d'arrivée")
    check_out = models.DateTimeField(blank=True, null=True, verbose_name="Heure de départ")

    class Meta:
        verbose_name = "Présence"
        verbose_name_plural = "Présences"
        unique_together = ('application', 'date')
        ordering = ['date']

    def __str__(self):
        status = "Présent" if self.present else "Absent"
        return f"{self.application.user} - {self.date} ({status})"

    @property
    def duration(self):
        if self.check_in and self.check_out:
            return self.check_out - self.check_in
        return None


class EventDate(models.Model):
    """Dates spécifiques pour les événements récurrents"""
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='attendance_dates',
        verbose_name="Événement"
    )
    date = models.DateField(verbose_name="Date de session")

    class Meta:
        verbose_name = "Date d'événement"
        verbose_name_plural = "Dates d'événement"
        unique_together = ('event', 'date')
        ordering = ['date']

    def __str__(self):
        return f"{self.event.title} - {self.date}"


class Report(models.Model):
    REPORT_TYPE_CHOICES = [
        ('PARTICIPATION', 'Rapport de participation'),
        ('ATTENDANCE', 'Rapport de présence'),
        ('EVENT', 'Rapport d\'événement'),
        ('USER', 'Rapport utilisateur'),
        ('FINANCIAL', 'Rapport financier'),
    ]

    # Métadonnées
    title = models.CharField(max_length=255, verbose_name="Titre du rapport")
    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPE_CHOICES,
        default='PARTICIPATION',
        verbose_name="Type de rapport"
    )
    description = models.TextField(blank=True, null=True, verbose_name="Description")

    # Paramètres
    start_date = models.DateField(verbose_name="Date de début")
    end_date = models.DateField(verbose_name="Date de fin")
    event = models.ForeignKey(
        Event,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Événement spécifique"
    )
    tags = TaggableManager(blank=True, verbose_name="Filtres par tags")

    # Fichier généré
    generated_file = models.FileField(
        upload_to='reports/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name="Fichier généré"
    )

    # Suivi
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_reports',
        verbose_name="Créé par"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Rapport"
        verbose_name_plural = "Rapports"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_report_type_display()})"

    @property
    def date_range(self):
        return f"{self.start_date} - {self.end_date}"
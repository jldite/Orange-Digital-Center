from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class EventRegistration(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('CONFIRMED', 'Confirmé'),
        ('CANCELLED', 'Annulé'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='frontoffice_registrations',
        verbose_name="Utilisateur"
    )
    event = models.ForeignKey(
        'backoffice.Event',
        on_delete=models.CASCADE,
        related_name='frontoffice_registrations',
        verbose_name="Événement"
    )
    #relation vers l'inscription backoffice
    backoffice_application = models.OneToOneField(
        'backoffice.Application',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='frontoffice_counterpart',
        verbose_name="Application Backoffice"
    )
    # Nouveau champ pour lier à l'inscription backoffice
    backoffice_registration = models.OneToOneField(
        'events.Registration',
        related_name='frontoffice_registration',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Inscription Backoffice"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="Statut"
    )
    registration_date = models.DateTimeField(auto_now_add=True, verbose_name="Date d'inscription")
    attended = models.BooleanField(default=False, verbose_name="A participé")

    class Meta:
        verbose_name = "Inscription Frontoffice"
        verbose_name_plural = "Inscriptions Frontoffice"
        unique_together = ('user', 'event')

    def __str__(self):
        return f"{self.user} - {self.event}"

class UserProfile(models.Model):
    """Profil complémentaire pour les utilisateurs (frontoffice)"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='frontoffice_profile',
        verbose_name="Utilisateur"
    )
    interests = models.TextField(blank=True, null=True, verbose_name="Centres d'intérêt")
    skills = models.TextField(blank=True, null=True, verbose_name="Compétences")
    newsletter_subscribed = models.BooleanField(default=True, verbose_name="Abonné à la newsletter")

    class Meta:
        verbose_name = "Profil Frontoffice"
        verbose_name_plural = "Profils Frontoffice"

    def __str__(self):
        return f"Profil de {self.user.username}"


class Feedback(models.Model):
    """Retours d'expérience sur les événements"""
    RATING_CHOICES = [
        (1, '1 - Très mauvais'),
        (2, '2 - Mauvais'),
        (3, '3 - Moyen'),
        (4, '4 - Bon'),
        (5, '5 - Excellent'),
    ]

    event = models.ForeignKey(
        'backoffice.Event',
        on_delete=models.CASCADE,
        related_name='feedbacks',
        verbose_name="Événement"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='feedbacks',
        verbose_name="Utilisateur"
    )
    rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        verbose_name="Évaluation"
    )
    comment = models.TextField(verbose_name="Commentaire")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        verbose_name = "Feedback"
        verbose_name_plural = "Feedbacks"
        ordering = ['-created_at']

    def __str__(self):
        return f"Feedback sur {self.event.title} par {self.user.username if self.user else 'Anonyme'}"
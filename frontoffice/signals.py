from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import EventRegistration
from backoffice.models import Application


@receiver(post_save, sender=EventRegistration)
def sync_with_backoffice(sender, instance, created, **kwargs):
    if created:
        # Créer une inscription correspondante dans le backoffice
        backoffice_app = Application.objects.create(
            event=instance.event,
            user=instance.user,
            status='PENDING'  # Statut par défaut
        )

        # Lier les deux inscriptions
        instance.backoffice_application = backoffice_app
        instance.save()

        # Stocker l'ID frontoffice dans le modèle backoffice
        backoffice_app.frontoffice_registration_id = instance.id
        backoffice_app.save()
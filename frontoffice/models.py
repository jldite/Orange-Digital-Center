from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # — Types d’utilisateurs —
    ADMIN = 'admin'
    STAFF = 'staff'
    LEARNER = 'learner'
    USER_TYPE_CHOICES = (
        (ADMIN, 'Administrateur'),
        (STAFF, 'Équipe ODC'),
        (LEARNER, 'Apprenant'),
    )
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        blank=True,
        null=True,
    )

    # — Genre —
    GENDER_MALE = 'M'
    GENDER_FEMALE = 'F'
    GENDER_OTHER = 'O'
    GENDER_CHOICES = (
        (GENDER_MALE, 'Masculin'),
        (GENDER_FEMALE, 'Féminin'),
        (GENDER_OTHER, 'Autre'),
    )
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        blank=True,
        null=True,
    )

    # — Informations complémentaires —
    university = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    qr_code = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.username

    @property
    def is_admin(self):
        return self.user_type == self.ADMIN or self.is_superuser

    @property
    def is_staff_member(self):
        return self.user_type in {self.ADMIN, self.STAFF} or self.is_staff

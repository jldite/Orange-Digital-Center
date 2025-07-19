from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    ADMIN = 'admin'
    STAFF = 'staff'
    LEARNER = 'learner'
    USER_TYPE_CHOICES = (
        (ADMIN, 'Administrateur'),
        (STAFF, 'Équipe ODC'),
        (LEARNER, 'Apprenant'),
    )

    GENDER_MALE = 'M'
    GENDER_FEMALE = 'F'
    GENDER_OTHER = 'O'
    GENDER_CHOICES = (
        (GENDER_MALE, 'Masculin'),
        (GENDER_FEMALE, 'Féminin'),
        (GENDER_OTHER, 'Autre'),
    )

    username = models.CharField(max_length=150, unique=True)

    user_type = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )
    gender = models.CharField(
        max_length=1,
        blank=True,
        null=True
    )
    qr_code = models.CharField(max_length=100, blank=True, null=True)

    @property
    def is_admin(self):
        return self.user_type in [self.ADMIN, 'superuser'] or self.is_superuser

    @property
    def is_staff_member(self):
        return self.user_type in [self.ADMIN, self.STAFF] or self.is_staff

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('student', 'Étudiant'),
        ('entrepreneur', 'Entrepreneur'),
        ('startup', 'Startup'),
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    university = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20)
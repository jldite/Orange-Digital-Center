from django.contrib.auth.models import AbstractUser, Group, Permission
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

    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs',
        related_name= "custom_user_set",
        related_query_name= "user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="custoom_user_set",
        related_query_name="user",
    )
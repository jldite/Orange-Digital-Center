from django.db import models
from django.conf import settings
import uuid
from io import BytesIO
from django.core.files.base import ContentFile
import qrcode

# Définir les choix avant les modèles
STATUS_CHOICES = [
    ('pending', 'En attente'),
    ('approved', 'Approuvé'),
    ('rejected', 'Rejeté'),
]

LOCATION_CHOICES = [
    ('digital', 'Digital'),
    ('fablab', 'Fab Lab'),
    ('fab', 'Fab'),
    ('odc_clubs', 'ODC Clubs'),
]


class Event(models.Model):
    EVENT_TYPES = [
        ('formation', 'Formation'),
        ('conference', 'Conférence'),
        ('talk', 'Talk'),
        ('open_lab', 'Open Lab'),
        ('fab_cafe', 'Fab Café'),
        ('master_class', 'Master Class'),
        ('atelier', 'Atelier'),
        ('super_codeurs', 'Super Codeurs'),
        ('maker_junior', 'Maker Junior'),
    ]

    title = models.CharField(max_length=200)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    location = models.CharField(max_length=50, choices=LOCATION_CHOICES)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    description = models.TextField()

    def _str_(self):
        return self.title


class Registration(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    registration_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')  # Correction ici
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True)  # Correction du nom "qr_code" (pas "qp_code")

    def save(self, *args, **kwargs):
        if not self.qr_code:  # Générer le QR code seulement s'il n'existe pas
            self.generate_qr_code()
        super().save(*args, **kwargs)

    def generate_qr_code(self):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        # Données uniques pour le QR code
        unique_id = uuid.uuid4().hex
        data = f"REG:{self.id}:{self.user.id}:{unique_id}"
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')

        filename = f'qr_{self.user.username}_{self.event.id}.png'
        self.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)
        buffer.close()
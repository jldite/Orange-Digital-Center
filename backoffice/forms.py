from django import forms
from events.models import Event
from django.utils.translation import gettext_lazy as _


class EventForm(forms.ModelForm):
    generate_qr = forms.BooleanField(
        required=False,
        initial=True,
        label=_("Générer un QR Code pour cet événement")
    )

    # Ajoutez ces champs manquants
    contact_person = forms.CharField(required=False, max_length=100)
    contact_email = forms.EmailField(required=False)
    tracking_number = forms.CharField(required=False, max_length=50)
    priority = forms.ChoiceField(
        choices=Event.PRIORITY_CHOICES,
        initial='MEDIUM',
        required=False
    )

    class Meta:
        model = Event
        fields = [
            'title', 'description', 'type', 'location', 'cover_image',
            'start_date', 'end_date', 'registration_deadline',  # AJOUTEZ CE CHAMP
            'capacity', 'is_published', 'requires_approval',
            'tags',  # AJOUTEZ CE CHAMP
            'generate_qr'
        ]
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'registration_deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),  # AJOUTEZ CE WIDGET
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        registration_deadline = cleaned_data.get('registration_deadline')

        # Validation des dates
        if start_date and end_date and start_date >= end_date:
            self.add_error('end_date', "La date de fin doit être postérieure à la date de début")

        # Validation de la date limite d'inscription
        if start_date and registration_deadline and registration_deadline > start_date:
            self.add_error('registration_deadline',
                           "La date limite d'inscription doit être antérieure à la date de début")

        return cleaned_data
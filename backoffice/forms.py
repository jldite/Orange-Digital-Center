from django import forms
from events.models import Event
from django.utils.translation import gettext_lazy as _


class EventForm(forms.ModelForm):
    generate_qr = forms.BooleanField(
        required=False,
        initial=True,
        label=_("Générer un QR Code pour cet événement")
    )

    class Meta:
        model = Event
        fields = [
            'title', 'description', 'type', 'location', 'cover_image',
            'start_date', 'end_date', 'registration_deadline', 'capacity',
            'is_published', 'requires_approval', 'tags', 'generate_qr'
        ]
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'registration_deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'is_published': _('Publier immédiatement'),
            'requires_approval': _('Nécessite une approbation manuelle'),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        registration_deadline = cleaned_data.get('registration_deadline')

        # Validation des dates
        if start_date and end_date and start_date >= end_date:
            self.add_error('end_date', "La date de fin doit être postérieure à la date de début")

        if registration_deadline and start_date and registration_deadline > start_date:
            self.add_error('registration_deadline',
                           "La date limite d'inscription doit être antérieure au début de l'événement")

        return cleaned_data
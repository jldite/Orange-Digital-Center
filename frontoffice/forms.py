# frontoffice/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class FrontUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs.update({
            'id': 'prenom',
            'class': 'input-field',
            'placeholder': 'Votre prénom'
        })
        self.fields['last_name'].widget.attrs.update({
            'id': 'nom',
            'class': 'input-field',
            'placeholder': 'Votre nom'
        })
        self.fields['email'].widget.attrs.update({
            'id': 'email',
            'class': 'input-field',
            'placeholder': 'votre@email.com'
        })
        self.fields['username'].widget.attrs.update({
            'class': 'hidden'
        })
        self.fields['password1'].widget.attrs.update({
            'id': 'password',
            'class': 'input-field',
            'placeholder': '••••••••'
        })
        self.fields['password2'].widget.attrs.update({
            'id': 'confirm-password',
            'class': 'input-field',
            'placeholder': '••••••••'
        })

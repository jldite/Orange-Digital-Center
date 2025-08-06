from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django import forms
from django.contrib.auth import login, authenticate
from django.core.exceptions import ValidationError
from django.views import View

from backoffice.models import CustomUser


class home_view(View):
    def get(self,request):
        return render(request, 'frontoffice/home.html')

# Formulaire d'inscription personnalisé
class CustomUserCreationForm(forms.Form):
    nom = forms.CharField(max_length=30, required=True, label="Nom")
    postnom = forms.CharField(max_length=30, required=True, label="Postnom")
    email = forms.EmailField(required=True, label="Adresse email")
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=True,
        label="Mot de passe"
    )
    confirmPassword = forms.CharField(
        widget=forms.PasswordInput,
        required=True,
        label="Confirmer le mot de passe"
    )
    terms = forms.BooleanField(required=True, label="J'accepte les termes et conditions")

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirmPassword")

        if password and confirm_password and password != confirm_password:
            raise ValidationError("Les mots de passe ne correspondent pas")

        email = cleaned_data.get("email")
        # Utilisez le modèle CustomUser ici
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("Cette adresse email est déjà utilisée")

        return cleaned_data


def user_register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Création de l'utilisateur
            nom = form.cleaned_data['nom']
            postnom = form.cleaned_data['postnom']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Créer l'utilisateur avec le modèle CustomUser
            user = CustomUser.objects.create_user(
                username=email,  # Utiliser l'email comme nom d'utilisateur
                email=email,
                password=password,
                first_name=nom,
                last_name=postnom
            )

            # Authentifier et connecter automatiquement l'utilisateur
            authenticated_user = authenticate(
                request,
                username=email,
                password=password
            )

            if authenticated_user is not None:
                login(request, authenticated_user)
                messages.success(request, "Compte créé avec succès. Vous êtes maintenant connecté!")
                return redirect('frontoffice:home')
            else:
                messages.warning(request,
                                 "Compte créé mais connexion automatique échouée. Veuillez vous connecter manuellement.")
                return redirect('frontoffice:login')
        else:
            # Afficher les erreurs de validation
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    else:
        form = CustomUserCreationForm()

    return render(request, 'frontoffice/register.html', {'form': form})


# Vue de déconnexion
def user_logout(request):
    logout(request)
    messages.success(request, "Vous avez été déconnecté.")
    return redirect('frontoffice:home')


# Vue du profil (nécessite connexion)
@login_required
def user_profile(request):
    return render(request, 'frontoffice/profile.html', {'user': request.user})

def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    context = {'event': event}
    return render(request, 'events/event_detail.html', context)
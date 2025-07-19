from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views import View

class home_view(View):
    def get(self,request):
        return render(request, 'frontoffice/home.html')

def user_register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Compte créé avec succès. Veuillez vous connecter.")
            return redirect('login')
        else:
            messages.error(request, "Veuillez corriger les erreurs.")
    else:
        form = UserCreationForm()
    return render(request, 'frontoffice/registration.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Bienvenue {user.username} !")
            return redirect('profile')
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe invalide.")
    else:
        form = AuthenticationForm()
    return render(request, 'frontoffice/login.html', {'form': form})


# Vue de déconnexion
def user_logout(request):
    logout(request)
    messages.success(request, "Vous avez été déconnecté.")
    return redirect('login')


# Vue du profil (nécessite connexion)
@login_required
def user_profile(request):
    return render(request, 'frontoffice/profile.html', {'user': request.user})
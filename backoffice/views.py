# backoffice/views.py
import email

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from events.models import Event
from frontoffice.models import CustomUser
from applications.models import Application
from attendance.models import Attendance

# Fonction utilitaire pour vérifier les droits admin
def admin_required(user):
    """Vérifie si l'utilisateur est admin ou staff"""
    return user.is_authenticated and (user.is_staff or user.is_superuser or getattr(user, 'is_admin', False))


# ==============================================
# VUES D'AUTHENTIFICATION
# ==============================================

@csrf_protect
def admin_login(request):
    """Page de connexion pour l'administration"""
    # Rediriger si déjà connecté
    if request.user.is_authenticated and admin_required(request.user):
        return redirect('backoffice:backoffice_dashboard')

    if request.method == 'POST':
        print("CSRF token in from:", request.POST.get('csrfmiddlewaretoken', 'MISSING'))
        print("CSRF token in cookie:", request.META.get('CSRF_COOKIE', 'MISSING'))
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            messages.error(request, "Aucun compte associe a ce nom d'utilisateur")
        else:
            if user.check_password(password):
                if user.is_active and (user.is_staff or user.is_superuser):
                    login(request, user)
                    return redirect('backoffice:backoffice_dashboard')
                else:
                    if not user.is_active:
                        messages.error(request, "Ce compte est desactive")
                    else:
                        messages.error(request, "Vous n'avez pas les droits d'administrateur")
            else:
                messages.error(request, "Mot de passe incorrect")

    return render(request, 'backoffice/auth/login.html')


@login_required
def admin_logout(request):
    """Déconnexion de l'administration"""
    logout(request)
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return redirect('backoffice:admin_login')


# ==============================================
# VUES DU DASHBOARD ET BACKOFFICE
# ==============================================

@login_required
def backoffice_dashboard(request):
    """Tableau de bord principal"""
    if not admin_required(request.user):
        raise PermissionDenied

    # Statistiques principales
    total_events = Event.objects.count()
    upcoming_events = Event.objects.filter(start_date__gte=timezone.now()).count()
    total_users = CustomUser.objects.count()

    # Calcul du taux de participation par genre
    gender_data = CustomUser.objects.values('gender').annotate(
        count=Count('id')
    ).order_by('gender')

    # Préparer les données pour le graphique
    gender_labels = []
    gender_values = []
    for item in gender_data:
        gender_labels.append(dict(CustomUser.GENDER_CHOICES).get(item['gender'], item['gender']))
        gender_values.append(item['count'])

    # Derniers événements
    recent_events = Event.objects.all().order_by('-start_date')[:5]

    context = {
        'total_events': total_events,
        'upcoming_events': upcoming_events,
        'total_users': total_users,
        'gender_labels': gender_labels,
        'gender_values': gender_values,
        'recent_events': recent_events,
    }
    return render(request, 'backoffice/dashboard/dashboard.html', context)


@login_required
def event_list(request):
    """Liste des événements"""
    if not admin_required(request.user):
        raise PermissionDenied

    events = Event.objects.all().order_by('-start_date')
    return render(request, 'backoffice/events/list.html', {'events': events})


@login_required
def event_create(request):
    """Création d'un nouvel événement"""
    if not admin_required(request.user):
        raise PermissionDenied

    # Logique de création d'événement
    # ...
    return render(request, 'backoffice/events/create.html')


@login_required
def event_edit(request, event_id):
    """Modification d'un événement"""
    if not admin_required(request.user):
        raise PermissionDenied

    # Logique d'édition d'événement
    # ...
    return render(request, 'backoffice/events/edit.html')


@login_required
def participant_list(request, event_id=None):
    """Liste des participants"""
    if not admin_required(request.user):
        raise PermissionDenied

    if event_id:
        participants = Application.objects.filter(event_id=event_id, status='approved')
    else:
        participants = Application.objects.filter(status='approved')

    return render(request, 'backoffice/participants/list.html', {'participants': participants})


# ==============================================
# VUES DE GESTION DES UTILISATEURS
# ==============================================

@login_required
def user_list(request):
    """Liste des utilisateurs"""
    if not admin_required(request.user):
        raise PermissionDenied

    users = CustomUser.objects.all().order_by('-date_joined')
    return render(request, 'backoffice/frontoffice/list.html', {'frontoffice': users})


@login_required
def user_detail(request, user_id):
    """Détail d'un utilisateur"""
    if user_id is None:
        user_id = request.user.id
    if not admin_required(request.user):
        raise PermissionDenied

    user = get_object_or_404(CustomUser, id=user_id)
    return render(request, 'backoffice/frontoffice/detail.html', {'user': user})


# ==============================================
# VUES DE RAPPORT ET ANALYTIQUE
# ==============================================

@login_required
def generate_report(request, report_type):
    """Génération de rapports"""
    if not admin_required(request.user):
        raise PermissionDenied

    # Logique de génération de rapport selon le type
    # ...
    return render(request, 'backoffice/reports/generate.html')


# ==============================================
# VUES D'ADMINISTRATION SYSTÈME
# ==============================================

@login_required
def system_settings(request):
    """Paramètres système"""
    if not request.user.is_superuser:
        raise PermissionDenied

    # Logique des paramètres système
    # ...
    return render(request, 'backoffice/system/settings.html')

def home_view(request):
    """Vue pour la page d'accueil"""
    return render(request, 'home.html')

@login_required
def profile(request):
    return user_detail(request, request.user.id)
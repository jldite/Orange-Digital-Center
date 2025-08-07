from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q, F
from events.models import Event
from backoffice.models import CustomUser
from applications.models import Application


def admin_required(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser or getattr(user, 'is_admin', False))

# ==============================================
# VUES D'AUTHENTIFICATION
# ==============================================

@csrf_protect
def login_view(request):
    """
    Formulaire unique pour admin ET utilisateur normal.
    Redirige selon le rôle.
    """
    if request.user.is_authenticated:
        if admin_required(request.user):
            return redirect('backoffice:backoffice_dashboard')
        # Redirection vers la page d'accueil publique
        return redirect('home')  # Changé ici

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is None:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
        elif not user.is_active:
            messages.error(request, "Ce compte est désactivé.")
        else:
            login(request, user)
            if admin_required(user):
                return redirect('backoffice:backoffice_dashboard')
            # Redirection vers la page d'accueil publique
            return redirect('home')  # Changé ici

    return render(request, 'backoffice/auth/login.html')
# ==============================================
# VUES DU DASHBOARD ET BACKOFFICE
# ==============================================
@login_required
def backoffice_dashboard(request):
    if not admin_required(request.user):
        raise PermissionDenied

    # Statistiques principales
    total_events = Event.objects.count()
    upcoming_events = Event.objects.filter(start_date__gte=timezone.now()).count()
    total_users = CustomUser.objects.count()
    approved_applications = Application.objects.filter(status='approved').count()
    total_applications = Application.objects.count()

    # Calcul du taux de participation
    participation_rate = 0
    if total_applications > 0:
        participation_rate = round((approved_applications / total_applications) * 100)

    # Calcul du taux de satisfaction (exemple)
    satisfaction_rate = 4.5

    # Données pour graphique participation par genre
    gender_data = CustomUser.objects.values('gender').annotate(
        count=Count('id')
    ).order_by('gender')

    gender_labels = []
    gender_values = []
    for item in gender_data:
        gender_labels.append(dict(CustomUser.GENDER_CHOICES).get(item['gender'], item['gender']))
        gender_values.append(item['count'])

    # Données pour graphique événements par type
    event_types = Event.TYPE_CHOICES
    event_type_data = []
    event_type_labels = []
    for type_id, type_name in event_types:
        count = Event.objects.filter(event_type=type_id).count()
        event_type_data.append(count)
        event_type_labels.append(type_name)

    # Derniers événements
    recent_events = Event.objects.all().order_by('-start_date')[:5]

    # Calcul des variations
    last_month = timezone.now() - timezone.timedelta(days=30)
    events_last_month = Event.objects.filter(created_at__gte=last_month).count()
    events_variation = round(
        ((total_events - events_last_month) / events_last_month * 100)) if events_last_month > 0 else 0
    abs_events_variation = abs(events_variation)

    context = {
        'total_events': total_events,
        'upcoming_events': upcoming_events,
        'total_users': total_users,
        'participation_rate': participation_rate,
        'satisfaction_rate': satisfaction_rate,
        'gender_labels': gender_labels,
        'gender_values': gender_values,
        'event_type_labels': event_type_labels,
        'event_type_data': event_type_data,
        'recent_events': recent_events,
        'events_variation': events_variation,
        'approved_applications': approved_applications,
        'abs_events_variation': abs_events_variation,
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
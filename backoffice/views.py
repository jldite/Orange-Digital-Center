import io
import uuid

import qrcode
from django.core.files import File
from django.http import FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.template.defaultfilters import slugify
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q, F
from django.views.generic import CreateView

from events.models import Event
from backoffice.models import CustomUser
from applications.models import Application


def admin_required(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser or getattr(user, 'is_admin', False))

# ==============================================
# VUES D'AUTHENTIFICATION
# ==============================================

@csrf_exempt
def login_view(request):
    if request.user.is_authenticated:
        if admin_required(request.user):
            return redirect('backoffice:backoffice_dashboard')
        return redirect('home')

    if request.method == 'POST':
        identifier = request.POST.get('identifier')  # Champ unique pour username ou email
        password = request.POST.get('password')

        # Essayer d'abord avec le nom d'utilisateur
        user = authenticate(request, username=identifier, password=password)

        # Si échec, essayer avec l'email
        if user is None:
            try:
                user_obj = CustomUser.objects.get(email=identifier)
                user = authenticate(request, username=user_obj.username, password=password)
            except CustomUser.DoesNotExist:
                pass  # On continue avec user=None

        if user is None:
            messages.error(request, "Identifiant ou mot de passe incorrect.")
        elif not user.is_active:
            messages.error(request, "Ce compte est désactivé.")
        else:
            login(request, user)
            if admin_required(user):
                return redirect('backoffice:backoffice_dashboard')
            return redirect('frontoffice:home')

    return render(request, 'backoffice/auth/login.html')

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "Vous avez été déconnecté.")
    return redirect('frontoffice:home')
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


class EventForm:
    pass


class EventCreateView(CreateView):
    model = Event
    form_class = EventForm
    template_name = 'backoffice/event_form.html'
    success_url = reverse_lazy('backoffice:event_list')

    def form_valid(self, form):
        # Sauvegarde initiale de l'événement
        event = form.save(commit=False)

        # Générer un slug unique basé sur le titre
        event.slug = slugify(event.title)
        if Event.objects.filter(slug=event.slug).exists():
            event.slug = f"{event.slug}-{uuid.uuid4().hex[:6]}"

        # Sauvegarde finale pour obtenir un ID
        event.save()
        form.save_m2m()  # Pour les relations ManyToMany (tags)

        # Génération du QR Code si l'option est cochée
        if self.request.POST.get('generate_qr') == 'on':
            self.generate_qr_code(event)

        # Création du message de succès
        messages.success(
            self.request,
            f"L'événement '{event.title}' a été créé avec succès. "
            f"<a href='{reverse('backoffice:event_detail', args=[event.slug])}' class='text-orange-primary hover:underline'>Voir les détails</a>"
        )

        return super().form_valid(form)

    def generate_qr_code(self, event):
        """
        Génère un QR Code pour l'événement et l'enregistre dans le modèle
        """
        # Construction de l'URL publique de l'événement
        event_url = self.request.build_absolute_uri(
            reverse('front:event_detail', args=[event.slug])
        )

        # Création du QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(event_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Sauvegarde de l'image dans un buffer
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")

        # Création du nom de fichier
        filename = f"event_qr_{event.id}_{event.slug}.png"

        # Sauvegarde dans le champ qr_code du modèle
        event.qr_code.save(filename, File(buffer), save=True)
        event.save()

        # Ajout d'un message informatif
        messages.info(
            self.request,
            f"Un QR Code a été généré pour l'événement. "
            f"<a href='{event.qr_code.url}' download class='text-orange-primary hover:underline'>Télécharger</a>"
        )

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

@login_required
def qr_codes_view(request):
    events = Event.objects.all()
    return render(request, 'backoffice/dashboard/qr_codes.html', {'events': events})

@login_required
def download_qr(request, event_id):
    event = Event.objects.get(id=event_id)

    # Générer le QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(f"event:{event.id}")
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Créer une réponse fichier
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return FileResponse(buffer, as_attachment=True, filename=f"qr_code_event_{event.id}.png")
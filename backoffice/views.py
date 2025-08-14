import io
import uuid
import csv
import datetime

import qrcode
from django.core.files import File
from django.core.files.base import ContentFile
from django.http import FileResponse, HttpResponse, HttpResponseRedirect
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
from django.views.generic import CreateView, UpdateView, DetailView

from events.models import Event
from backoffice.models import CustomUser
from applications.models import Application
from .forms import EventForm


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
        identifier = request.POST.get('identifier')
        password = request.POST.get('password')

        user = authenticate(request, username=identifier, password=password)

        if user is None:
            try:
                user_obj = CustomUser.objects.get(email=identifier)
                user = authenticate(request, username=user_obj.username, password=password)
            except CustomUser.DoesNotExist:
                pass

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

    participation_rate = 0
    if total_applications > 0:
        participation_rate = round((approved_applications / total_applications) * 100)

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
    event_types = Event._meta.get_field('type').choices
    event_type_data = []
    event_type_labels = []
    for type_id, type_name in event_types:
        count = Event.objects.filter(type=type_id).count()
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


# ==============================================
# VUES DE GESTION DES ÉVÉNEMENTS
# ==============================================

def generate_qr_code(event, request):
    """Génère un QR Code pour l'événement"""
    event_url = request.build_absolute_uri(
        reverse('front:event_detail', args=[event.slug])
    )

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(event_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#FF7900", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    file_name = f"qr_event_{event.id}.png"

    event.qr_code.save(file_name, ContentFile(buffer.getvalue()), save=True)


@login_required
def event_list(request):
    """Liste des événements"""
    if not admin_required(request.user):
        raise PermissionDenied

    # Filtrer et trier les événements
    events = Event.objects.all().order_by('-start_date')

    # Filtrage par type
    event_type = request.GET.get('type')
    if event_type:
        events = events.filter(type=event_type)

    # Filtrage par statut
    status = request.GET.get('status')
    if status:
        events = events.filter(status=status)

    # Filtrage par date
    date_filter = request.GET.get('date_filter')
    if date_filter == 'upcoming':
        events = events.filter(start_date__gte=timezone.now())
    elif date_filter == 'past':
        events = events.filter(end_date__lt=timezone.now())

    context = {
        'events': events,
        'event_types': Event.TYPE_CHOICES,
        'status_choices': Event.STATUS_CHOICES,
        'selected_type': event_type,
        'selected_status': status,
        'selected_date': date_filter
    }
    return render(request, 'backoffice/events/list.html', context)


@login_required
def event_create(request):
    if not admin_required(request.user):
        raise PermissionDenied

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user

            # Générer le slug
            event.slug = slugify(event.title)
            if Event.objects.filter(slug=event.slug).exists():
                event.slug = f"{event.slug}-{uuid.uuid4().hex[:6]}"

            event.save()
            form.save_m2m()  # Pour les tags

            # Génération du QR Code
            if form.cleaned_data.get('generate_qr'):
                generate_qr_code(event, request)

            messages.success(request, f"Événement '{event.title}' créé avec succès !")
            return redirect('backoffice:event_list')
    else:
        form = EventForm(initial={
            'capacity': 50,
            'is_published': True,
            'generate_qr': True,
            'priority': 'MEDIUM'
        })

    return render(request, 'backoffice/events/create.html', {'form': form})


@login_required
def event_edit(request, pk):
    """Modification d'un événement"""
    if not admin_required(request.user):
        raise PermissionDenied

    event = get_object_or_404(Event, pk=pk)

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            updated_event = form.save(commit=False)

            # Validation des dates
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            registration_deadline = form.cleaned_data['registration_deadline']

            if start_date >= end_date:
                messages.error(request, "La date de fin doit être postérieure à la date de début.")
                return render(request, 'backoffice/events/edit.html', {'form': form, 'event': event})

            if registration_deadline > start_date:
                messages.error(request, "La date limite d'inscription doit être antérieure à la date de début.")
                return render(request, 'backoffice/events/edit.html', {'form': form, 'event': event})

            # Générer un nouveau QR Code si demandé et non existant
            if form.cleaned_data.get('generate_qr') and not event.qr_code:
                generate_qr_code(updated_event, request)

            updated_event.save()
            form.save_m2m()  # Pour les tags

            messages.success(request, f"Événement '{updated_event.title}' mis à jour avec succès !")
            return redirect('backoffice:event_detail', pk=event.pk)
    else:
        form = EventForm(instance=event)

    return render(request, 'backoffice/events/edit.html', {'form': form, 'event': event})


@login_required
def event_detail(request, pk):
    """Détails d'un événement"""
    if not admin_required(request.user):
        raise PermissionDenied

    event = get_object_or_404(Event, pk=pk)
    participants = Application.objects.filter(event=event, status='approved')

    # Statistiques de participation
    total_capacity = event.capacity
    registered_count = participants.count()
    participation_percentage = round((registered_count / total_capacity * 100)) if total_capacity > 0 else 0

    # Répartition par genre
    gender_distribution = participants.values('user__gender').annotate(count=Count('id'))

    context = {
        'event': event,
        'participants': participants,
        'registered_count': registered_count,
        'participation_percentage': participation_percentage,
        'gender_distribution': gender_distribution,
        'available_spots': total_capacity - registered_count,
        'attendance_rate': round(
            (participants.filter(attended=True).count() / registered_count * 100)) if registered_count > 0 else 0,
    }
    return render(request, 'backoffice/events/detail.html', context)


@login_required
def event_delete(request, pk):
    """Suppression d'un événement"""
    if not admin_required(request.user):
        raise PermissionDenied

    event = get_object_or_404(Event, pk=pk)

    if request.method == 'POST':
        event_title = event.title
        event.delete()
        messages.success(request, f"Événement '{event_title}' supprimé avec succès !")
        return redirect('backoffice:event_list')

    return render(request, 'backoffice/events/delete_confirm.html', {'event': event})


# ==============================================
# VUES DE GESTION DES PARTICIPANTS
# ==============================================

@login_required
def participant_list(request, event_id=None):
    """Liste des participants"""
    if not admin_required(request.user):
        raise PermissionDenied

    if event_id:
        event = get_object_or_404(Event, id=event_id)
        participants = Application.objects.filter(event=event, status='approved')
    else:
        participants = Application.objects.filter(status='approved')
        event = None

    # Filtres
    status_filter = request.GET.get('status')
    if status_filter:
        participants = participants.filter(status=status_filter)

    gender_filter = request.GET.get('gender')
    if gender_filter:
        participants = participants.filter(user__gender=gender_filter)

    context = {
        'participants': participants,
        'event': event,
        'status_choices': Application.STATUS_CHOICES,
        'gender_choices': CustomUser.GENDER_CHOICES,
        'selected_status': status_filter,
        'selected_gender': gender_filter
    }
    return render(request, 'backoffice/participants/list.html', context)


@login_required
def export_participants_csv(request, event_id=None):
    """Export CSV des participants"""
    if not admin_required(request.user):
        raise PermissionDenied

    if event_id:
        participants = Application.objects.filter(event_id=event_id, status='approved')
        filename = f"participants_event_{event_id}.csv"
    else:
        participants = Application.objects.filter(status='approved')
        filename = "tous_les_participants.csv"

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Événement', 'Nom', 'Prénom', 'Email',
        'Téléphone', 'Genre', 'Statut', 'Date inscription'
    ])

    for p in participants:
        writer.writerow([
            p.id,
            p.event.title,
            p.user.last_name,
            p.user.first_name,
            p.user.email,
            p.user.phone_number,
            p.user.get_gender_display(),
            p.get_status_display(),
            p.created_at.strftime("%d/%m/%Y %H:%M")
        ])

    return response


# ==============================================
# VUES DE GESTION DES UTILISATEURS
# ==============================================

@login_required
def user_list(request):
    """Liste des utilisateurs"""
    if not admin_required(request.user):
        raise PermissionDenied

    users = CustomUser.objects.all().order_by('-date_joined')

    # Filtres
    role_filter = request.GET.get('role')
    if role_filter:
        if role_filter == 'admin':
            users = users.filter(is_staff=True)
        elif role_filter == 'user':
            users = users.filter(is_staff=False)

    context = {
        'users': users,
        'selected_role': role_filter
    }
    return render(request, 'backoffice/users/list.html', context)


@login_required
def user_detail(request, pk):
    """Détail d'un utilisateur"""
    if not admin_required(request.user):
        raise PermissionDenied

    user = get_object_or_404(CustomUser, pk=pk)
    applications = Application.objects.filter(user=user)

    context = {
        'user': user,
        'applications': applications,
        'approved_count': applications.filter(status='approved').count(),
        'pending_count': applications.filter(status='pending').count(),
        'rejected_count': applications.filter(status='rejected').count()
    }
    return render(request, 'backoffice/users/detail.html', context)


# ==============================================
# VUES DE RAPPORT ET ANALYTIQUE
# ==============================================

@login_required
def generate_report(request, report_type):
    """Génération de rapports"""
    if not admin_required(request.user):
        raise PermissionDenied

    # Déterminer la période
    today = timezone.now().date()
    start_date = request.GET.get('start_date', (today - timezone.timedelta(days=30)).isoformat())
    end_date = request.GET.get('end_date', today.isoformat())

    # Convertir en objets date
    try:
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        start_date = today - timezone.timedelta(days=30)
        end_date = today

    context = {
        'report_type': report_type,
        'start_date': start_date,
        'end_date': end_date
    }

    if report_type == 'events':
        events = Event.objects.filter(
            start_date__date__gte=start_date,
            start_date__date__lte=end_date
        )
        context['events'] = events
        return render(request, 'backoffice/reports/events_report.html', context)

    elif report_type == 'participants':
        participants = Application.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
            status='approved'
        )
        context['participants'] = participants
        return render(request, 'backoffice/reports/participants_report.html', context)

    elif report_type == 'attendance':
        # Calculer le taux de participation par événement
        events = Event.objects.filter(
            start_date__date__gte=start_date,
            start_date__date__lte=end_date
        ).annotate(
            total_participants=Count('applications'),
            attended_count=Count('applications', filter=Q(applications__attended=True))
        )

        for event in events:
            if event.total_participants > 0:
                event.attendance_rate = round((event.attended_count / event.total_participants) * 100)
            else:
                event.attendance_rate = 0

        context['events'] = events
        return render(request, 'backoffice/reports/attendance_report.html', context)

    return render(request, 'backoffice/reports/generate.html', context)


# ==============================================
# VUES D'ADMINISTRATION SYSTÈME
# ==============================================

@login_required
def system_settings(request):
    """Paramètres système"""
    if not request.user.is_superuser:
        raise PermissionDenied

    return render(request, 'backoffice/system/settings.html')


# ==============================================
# VUES DIVERSES
# ==============================================

def home_view(request):
    """Vue pour la page d'accueil"""
    return render(request, 'home.html')


@login_required
def profile(request):
    return user_detail(request, request.user.id)


@login_required
def qr_codes_view(request):
    events = Event.objects.exclude(qr_code='').order_by('-start_date')
    return render(request, 'backoffice/events/qr_codes.html', {'events': events})


@login_required
def download_qr(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    # Si le QR code n'existe pas, le générer
    if not event.qr_code:
        generate_qr_code(event, request)

    response = FileResponse(event.qr_code.open(), as_attachment=True, filename=f"qr_code_{event.slug}.png")
    return response


@login_required
def download_all_qr_codes(request):
    events = Event.objects.exclude(qr_code='')

    # Créer une archive ZIP si nécessaire
    # (Implémentation simplifiée pour l'exemple)
    response = HttpResponse(content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="tous_les_qr_codes.zip"'

    # Dans une implémentation réelle, vous utiliseriez le module zipfile
    # pour créer une archive contenant tous les QR codes

    return response
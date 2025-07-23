from django.urls import path
from . import views

app_name = 'backoffice'

urlpatterns = [
    # Authentification
    path('login/', views.login_view, name='login'),
    path('logout/', views.admin_logout, name='logout'),

    # Dashboard
    path('dashboard/', views.backoffice_dashboard, name='backoffice_dashboard'),

    # Gestion des événements
    path('events/', views.event_list, name='event_list'),
    path('events/create/', views.event_create, name='event_create'),
    path('events/<int:event_id>/edit/', views.event_edit, name='event_edit'),

    # Gestion des participants
    path('participants/', views.participant_list, name='participant_list'),
    path('events/<int:event_id>/participants/', views.participant_list, name='event_participant_list'),

    # Gestion des utilisateurs
    path('frontoffice/', views.user_list, name='user_list'),
    path('frontoffice/<int:user_id>/', views.user_detail, name='user_detail'),

    # Rapports
    path('reports/<str:report_type>/', views.generate_report, name='generate_report'),

    # Administration système (superadmin seulement)
    path('system/settings/', views.system_settings, name='system_settings'),
    # Profile
    path('profile/', views.user_detail, name='profile', kwargs={'user_id':None}),
]
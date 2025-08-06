from django.urls import path

from backoffice.views import login_view
from . import views
from django.views.generic import TemplateView

app_name = 'frontoffice'

urlpatterns = [
    path('', TemplateView.as_view(template_name='frontoffice/home.html'), name='home'),
    path('login/', login_view, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.user_register, name='register'),
    path('profile/', views.user_profile, name='profile'),
    #path('events/<int:event_id>/', views.event_detail, name='event_detail'),
    #path('events/<int:event_id>/register/', views.register_for_event, name='event_register'),
    #path('registrations/<int:registration_id>/confirmation/', views.registration_confirmation, name='registration_confirmation'),
]
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
]
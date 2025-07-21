"""
URL configuration for OrangeDigitalCenter project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.views.generic import RedirectView

from backoffice.views import home_view

urlpatterns = [
    path('', include('frontoffice.urls', namespace='frontoffice')),
    path('backoffice/', include('backoffice.urls')),
    path('admin-login/', RedirectView.as_view(url='/backoffice/login/')),
]
from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'frontoffice'

class FrontofficeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'frontoffice'

    def ready(self):
        import frontoffice.signals
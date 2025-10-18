from django.apps import AppConfig

class EmboucheConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'embouche'
    verbose_name = "Suivi embouche"


    def ready(self):
        from . import signals  # enregistre les receivers

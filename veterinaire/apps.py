# veterinaire/apps.py
from django.apps import AppConfig

class VeterinaireConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "veterinaire"
    verbose_name = "Module Vétérinaire"

    def ready(self):
        # Importer les signaux ici pour éviter les imports circulaires
        from . import signals  # noqa: F401

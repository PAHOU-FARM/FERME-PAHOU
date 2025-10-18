# naissance/apps.py
from django.apps import AppConfig

class NaissanceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "naissance"
    verbose_name = "Naissances"

    def ready(self):
        # importe les receveurs de signaux
        from . import signals  # noqa

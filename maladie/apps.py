from django.apps import AppConfig

class MaladieConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'maladie'
    verbose_name = "Gestion des maladies"

    def ready(self):
        from . import signals  # noqa
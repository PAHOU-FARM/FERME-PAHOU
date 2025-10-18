from django.apps import AppConfig

class VenteConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vente'
    verbose_name = "Suivi des ventes"


    def ready(self):
        from . import signals  # noqa

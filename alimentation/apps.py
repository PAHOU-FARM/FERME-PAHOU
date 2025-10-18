from django.apps import AppConfig

class AlimentationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "alimentation"
    verbose_name = "Gestion de l'alimentation"

    def ready(self):
        import alimentation.signals

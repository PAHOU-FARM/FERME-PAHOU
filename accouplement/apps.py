from django.apps import AppConfig

class AccouplementConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accouplement"
    verbose_name = "Gestion des accouplements"


    def ready(self):
        import accouplement.signals

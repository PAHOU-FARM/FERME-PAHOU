from django.apps import AppConfig

class VaccinationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vaccination'
    verbose_name = "Gestion des vaccinations"


    def ready(self):
        import vaccination.signals  # noqa: F401
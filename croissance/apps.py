from django.apps import AppConfig


class CroissanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'croissance'
    verbose_name = "Suivi croissance"


    def ready(self):
        import croissance.signals
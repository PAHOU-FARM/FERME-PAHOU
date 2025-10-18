from django.apps import AppConfig


class ReproductionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reproduction'
    verbose_name = "Cycles de reproduction"


    def ready(self):
        import reproduction.signals

from django.apps import AppConfig

class HistoriquetroupeauConfig(AppConfig):
    name = 'historiquetroupeau'
    verbose_name = "Historique du troupeau"

    def ready(self):
        import troupeau.signals  # enregistre les receivers

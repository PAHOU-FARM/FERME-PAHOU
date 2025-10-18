from django.apps import AppConfig

class TroupeauConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'troupeau'
    verbose_name = "Gestion du troupeau"

    def ready(self):
        # Ne plus importer troupeau.signals ici (on centralise dans historiquetroupeau)
        pass

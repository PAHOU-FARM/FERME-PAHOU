from django.apps import AppConfig

class GestationConfig(AppConfig):
  default_auto_field = 'django.db.models.BigAutoField'
  name = 'gestation'
  verbose_name = "Suivi des gestations"

  def ready(self):
      from . import signals  # enregistre les receivers

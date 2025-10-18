# naissance/signals.py
import logging
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Naissance

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Naissance)
def after_naissance_save(sender, instance: Naissance, created: bool, **kwargs):
    """
    Log léger après création/mise à jour d'une Naissance.
    Utilise on_commit pour n’agir qu’après commit de la transaction.
    """
    def _log():
        try:
            if created:
                logger.info("Nouvelle naissance enregistrée: %s (mère=%s, date=%s)",
                            instance.pk,
                            getattr(instance.boucle_mere, "boucle_ovin", instance.boucle_mere_id),
                            instance.date_mise_bas)
            else:
                logger.info("Naissance mise à jour: %s", instance.pk)
        except Exception as e:
            logger.exception("Post-save naissance: erreur lors du logging (%s)", e)

    # Exécute le log après commit (sécurise contre les rollbacks)
    transaction.on_commit(_log)

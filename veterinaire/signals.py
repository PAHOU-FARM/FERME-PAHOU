# veterinaire/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import logging

from .models import Veterinaire

logger = logging.getLogger(__name__)


def _boucle_from_instance(instance: Veterinaire):
    """
    Récupère un identifiant lisible de l'animal (boucle) sans faire planter
    si la FK n'est pas chargée/disponible (ex: en post_delete).
    """
    try:
        # Si la FK est accessible, on préfère la boucle
        boucle = getattr(getattr(instance, "troupeau", None), "boucle_ovin", None)
        return boucle or instance.troupeau_id
    except Exception:
        return instance.troupeau_id


@receiver(post_save, sender=Veterinaire, dispatch_uid="veterinaire_post_save")
def action_apres_sauvegarde_veterinaire(sender, instance: Veterinaire, created: bool, **kwargs):
    """
    Journalise la création/mise à jour d'une visite vétérinaire.
    Ignore les sauvegardes 'raw' (fixtures, migrations).
    """
    if kwargs.get("raw"):
        return

    boucle = _boucle_from_instance(instance)
    if created:
        logger.info(
            "Nouvelle visite vétérinaire (id=%s, animal=%s, date=%s, veto=%s)",
            instance.pk, boucle, instance.date_visite, instance.nom_veterinaire
        )
    else:
        logger.info(
            "Visite vétérinaire mise à jour (id=%s, animal=%s, date=%s, veto=%s)",
            instance.pk, boucle, instance.date_visite, instance.nom_veterinaire
        )


@receiver(post_delete, sender=Veterinaire, dispatch_uid="veterinaire_post_delete")
def action_apres_suppression_veterinaire(sender, instance: Veterinaire, **kwargs):
    """
    Journalise la suppression d'une visite vétérinaire.
    """
    boucle = _boucle_from_instance(instance)
    logger.info(
        "Visite vétérinaire supprimée (id=%s, animal=%s, date=%s, veto=%s)",
        instance.pk, boucle, instance.date_visite, instance.nom_veterinaire
    )

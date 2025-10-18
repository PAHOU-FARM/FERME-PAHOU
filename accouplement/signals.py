# accouplement/signals.py
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
import logging

from .models import Accouplement

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Accouplement, dispatch_uid="accouplement_set_reussi_flag")
def _set_reussi_flag(sender, instance: Accouplement, **kwargs):
    """
    Normalise le booléen accouplement_reussi avant sauvegarde:
    True seulement si vérification + date de gestation sont renseignées.
    """
    instance.accouplement_reussi = bool(
        instance.date_verification_gestation and instance.date_gestation
    )


@receiver(post_save, sender=Accouplement, dispatch_uid="accouplement_log_post_save")
def accouplement_post_save(sender, instance: Accouplement, created: bool, **kwargs):
    """
    Journalise la création/mise à jour et émet quelques alertes souples
    (sans bloquer) en cas d’incohérences possibles.
    """
    if created:
        logger.info("[Accouplement] Nouveau enregistré : %s", instance)
    else:
        logger.info("[Accouplement] Mis à jour : %s", instance)

    if instance.accouplement_reussi:
        logger.info(
            "[Accouplement RÉUSSI] %s x %s à partir du %s",
            getattr(instance.boucle_brebis, "boucle_ovin", instance.boucle_brebis_id),
            getattr(instance.boucle_belier, "boucle_ovin", instance.boucle_belier_id),
            instance.date_debut_lutte,
        )

    # Alerte douce : gestation sans fin de lutte
    if instance.date_gestation and not instance.date_fin_lutte:
        logger.warning(
            "[Incohérence] %s a une date de gestation sans date de fin de lutte.",
            instance,
        )

    # Alerte douce : fin de lutte avant début
    if (
        instance.date_fin_lutte
        and instance.date_debut_lutte
        and instance.date_fin_lutte < instance.date_debut_lutte
    ):
        logger.warning(
            "[Incohérence] Fin de lutte avant début pour %s.",
            instance,
        )

    # Alerte douce : gestation avant vérification
    if (
        instance.date_gestation
        and instance.date_verification_gestation
        and instance.date_gestation < instance.date_verification_gestation
    ):
        logger.warning(
            "[Incohérence] Gestation avant vérification pour %s.",
            instance,
        )

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
import logging

from .models import Vente

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Vente, dispatch_uid="vente_post_save")
def vente_created_or_updated(sender, instance: Vente, created: bool, **kwargs):
    """
    - Log la création/mise à jour d'une vente.
    - À la création : tente de marquer l'ovin comme vendu, désactive la boucle,
      et aligne date_sortie sur date_vente si ces champs existent sur Troupeau.
    """
    # Cas des chargements de fixtures/migrations
    if kwargs.get("raw"):
        return

    ovin = getattr(instance, "boucle_ovin", None)
    if not ovin:
        logger.warning("Vente #%s sans ovin associé.", instance.pk)
        return

    if created:
        logger.info(
            "✅ Nouvelle vente : ovin %s vendu le %s (vente #%s)",
            getattr(ovin, "boucle_ovin", ovin),
            instance.date_vente,
            instance.pk,
        )

        changed = set()

        # statut -> 'vendu' (si présent)
        if hasattr(ovin, "statut") and getattr(ovin, "statut", None) != "vendu":
            ovin.statut = "vendu"
            changed.add("statut")

        # boucle_active -> False (si présent)
        if hasattr(ovin, "boucle_active") and getattr(ovin, "boucle_active", True):
            ovin.boucle_active = False
            changed.add("boucle_active")

        # date_sortie -> date_vente (si présent)
        if hasattr(ovin, "date_sortie") and getattr(ovin, "date_sortie", None) != instance.date_vente:
            ovin.date_sortie = instance.date_vente
            changed.add("date_sortie")

        if changed:
            try:
                ovin.save(update_fields=list(changed))
            except Exception as exc:
                logger.warning(
                    "Échec de mise à jour ovin %s après vente #%s : %s",
                    getattr(ovin, "boucle_ovin", ovin),
                    instance.pk,
                    exc,
                )
    else:
        logger.info(
            "✏️ Vente mise à jour : ovin %s — vente #%s (date %s)",
            getattr(ovin, "boucle_ovin", ovin),
            instance.pk,
            instance.date_vente,
        )

        # Optionnel : si la date de vente change, on peut aligner date_sortie
        if hasattr(ovin, "date_sortie") and getattr(ovin, "date_sortie", None) != instance.date_vente:
            try:
                ovin.date_sortie = instance.date_vente
                ovin.save(update_fields=["date_sortie"])
            except Exception as exc:
                logger.warning(
                    "Impossible d'aligner date_sortie pour ovin %s : %s",
                    getattr(ovin, "boucle_ovin", ovin),
                    exc,
                )


@receiver(pre_delete, sender=Vente, dispatch_uid="vente_pre_delete")
def vente_deleted(sender, instance: Vente, **kwargs):
    """
    Log avant suppression d'une vente.
    (On ne réactive pas automatiquement l'ovin.)
    """
    ovin = getattr(instance, "boucle_ovin", None)
    logger.info(
        "❌ Suppression vente #%s — ovin %s (date %s)",
        instance.pk,
        getattr(ovin, "boucle_ovin", ovin) if ovin else "N/A",
        instance.date_vente,
    )

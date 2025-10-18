# maladie/signals.py
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils.timezone import now
import logging

from .models import Maladie

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Maladie)
def check_duplicate_maladie(sender, instance: Maladie, **kwargs):
    """
    Empêche les doublons exacts (Boucle, Nom, Date_obs, Symptômes, Traitement) :
    - À la création ET à la modification (on exclut l'instance courante via pk).
    Astuce : utile surtout si un champ du tuple est NULL (les DB autorisent
    plusieurs NULL dans un unique_together).
    """
    # Garde-fous (au cas où)
    if not instance.Boucle_Ovin_id or not instance.Date_observation:
        return

    qs = Maladie.objects.filter(
        Boucle_Ovin=instance.Boucle_Ovin,
        Nom_Maladie=instance.Nom_Maladie,
        Date_observation=instance.Date_observation,
        Symptomes_Observes=instance.Symptomes_Observes,
        Traitement_Administre=instance.Traitement_Administre,
    )
    if instance.pk:
        qs = qs.exclude(pk=instance.pk)

    if qs.exists():
        raise ValidationError(
            "Cette maladie avec les mêmes caractéristiques est déjà enregistrée pour cet animal."
        )


@receiver(post_save, sender=Maladie)
def alert_maladie_active_longue(sender, instance: Maladie, created, **kwargs):
    """
    Log d’alerte si une maladie reste 'Actif' depuis > 365 jours.
    N’influence pas la transaction (try/except large).
    """
    try:
        if instance.Statut == "Actif":
            delta_days = (now().date() - instance.Date_observation).days
            if delta_days > 365:
                logger.warning(
                    "[MALADIE - LONGUE DUREE] %s chez %s active depuis %s jours (depuis %s).",
                    instance.Nom_Maladie,
                    getattr(instance.Boucle_Ovin, "boucle_ovin", instance.Boucle_Ovin_id),
                    delta_days,
                    instance.Date_observation.isoformat(),
                )
    except Exception:
        # On ne bloque jamais la sauvegarde si le log échoue
        pass

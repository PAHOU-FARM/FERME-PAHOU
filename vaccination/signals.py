# vaccination/signals.py
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
import logging

from .models import Vaccination
from troupeau.models import Troupeau

logger = logging.getLogger(__name__)


# ───────────────────────────────────────────────────────────────────────────────
# Troupeau : désactiver la boucle si l'animal devient inactif
# ───────────────────────────────────────────────────────────────────────────────
@receiver(pre_save, sender=Troupeau)
def update_boucle_active(sender, instance: Troupeau, **kwargs):
    """
    Désactive automatiquement la boucle si le statut rend l’animal inactif.
    On tolère l'absence du champ 'statut' ou de 'boucle_active' sur le modèle.
    """
    statut_val = getattr(instance, "statut", None)
    if statut_val is None:
        return

    statut_norm = str(statut_val).strip().lower()
    inactifs = {"vendu", "decede", "décédé", "sortie", "mort"}

    if hasattr(instance, "boucle_active") and statut_norm in inactifs:
        instance.boucle_active = False


# ───────────────────────────────────────────────────────────────────────────────
# Vaccination : empêcher les doublons (même ovin, même date, même nom)
# ───────────────────────────────────────────────────────────────────────────────
@receiver(pre_save, sender=Vaccination)
def check_duplicate_vaccination(sender, instance: Vaccination, **kwargs):
    """
    Empêche un doublon de vaccination :
    même ovin, même date, même nom de vaccin (insensible à la casse).
    S'il manque un des trois éléments (ovin / date / nom), on ne contrôle pas.
    """
    ovin = getattr(instance, "boucle_ovin", None)
    date_vacc = getattr(instance, "date_vaccination", None)
    nom = (getattr(instance, "nom_vaccin", "") or "").strip()

    if not ovin or not date_vacc or not nom:
        return  # données incomplètes -> pas de contrôle de doublon

    qs = Vaccination.objects.filter(
        boucle_ovin=ovin,
        date_vaccination=date_vacc,
        nom_vaccin__iexact=nom,
    )
    if instance.pk:
        qs = qs.exclude(pk=instance.pk)

    if qs.exists():
        boucle_label = getattr(ovin, "boucle_ovin", getattr(ovin, "pk", ovin))
        raise ValidationError({
            "nom_vaccin": (
                f"Le vaccin « {nom} » est déjà enregistré pour l’ovin {boucle_label} "
                f"à la date du {date_vacc.strftime('%d/%m/%Y')}."
            )
        })


# ───────────────────────────────────────────────────────────────────────────────
# Vaccination : alerte si > 1 an depuis la précédente vaccination du même ovin
# ───────────────────────────────────────────────────────────────────────────────
@receiver(post_save, sender=Vaccination)
def alert_old_vaccination(sender, instance: Vaccination, created, **kwargs):
    """
    Log d’information si la précédente vaccination (même ovin) remonte à + d’1 an.
    S'applique uniquement lors de la création.
    """
    if not created:
        return

    ovin = getattr(instance, "boucle_ovin", None)
    date_vacc = getattr(instance, "date_vaccination", None)
    if not ovin or not date_vacc:
        return

    previous = (
        Vaccination.objects
        .filter(boucle_ovin=ovin)
        .exclude(pk=instance.pk)
        .order_by("-date_vaccination")
        .first()
    )

    if previous and previous.date_vaccination:
        delta_days = (date_vacc - previous.date_vaccination).days
        if delta_days > 365:
            logger.warning(
                "Plus d’un an depuis la dernière vaccination de %s : précédente le %s",
                getattr(ovin, "boucle_ovin", str(ovin)),
                previous.date_vaccination.isoformat(),
            )

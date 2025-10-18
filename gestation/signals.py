from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from .models import Gestation


@receiver(pre_save, sender=Gestation)
def verifier_gestation_confirmee(sender, instance: Gestation, **kwargs):
    """
    Validation avant sauvegarde d’une gestation.

    Règles :
    1) Interdit une nouvelle saisie NON confirmée si une gestation confirmée existe déjà.
    2) Interdit les doublons 'Non Confirmée' pour la même brebis et la même date.
    """

    # Champs alignés sur le modèle : date_gestation (snake_case)
    if not instance.boucle_brebis or not instance.date_gestation:
        # Laisse le modèle/form gérer le reste si champs manquants
        return

    brebis = instance.boucle_brebis
    d = instance.date_gestation

    # 1) Empêche une saisie non confirmée s’il existe déjà une confirmée
    if instance.etat_gestation != 'Confirmée':
        existe_confirmee = (
            Gestation.objects
            .filter(boucle_brebis=brebis, etat_gestation='Confirmée')
            .exclude(pk=instance.pk)
            .exists()
        )
        if existe_confirmee:
            raise ValidationError(
                f"La brebis {brebis} a déjà une gestation confirmée. "
                f"Aucune nouvelle saisie non confirmée n’est autorisée."
            )

    # 2) Un seul enregistrement 'Non Confirmée' par jour et par brebis
    if instance.etat_gestation == 'Non Confirmée':
        doublon_non_conf = (
            Gestation.objects
            .filter(boucle_brebis=brebis, date_gestation=d, etat_gestation='Non Confirmée')
            .exclude(pk=instance.pk)
            .exists()
        )
        if doublon_non_conf:
            raise ValidationError(
                f"Un suivi 'Non Confirmée' existe déjà pour la brebis {brebis} à la date {d}."
            )

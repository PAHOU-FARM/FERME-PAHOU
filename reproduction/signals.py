from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from accouplement.models import Accouplement
from gestation.models import Gestation
from naissance.models import Naissance
from .models import Reproduction


@receiver(post_save, sender=Accouplement)
def sync_reproduction_from_accouplement(sender, instance, created, **kwargs):
    """
    Crée/maj la Reproduction liée à un Accouplement.
    Champs cohérents avec le modèle Accouplement : boucle_brebis / boucle_belier.
    """
    femelle = instance.boucle_brebis
    male = instance.boucle_belier

    if created:
        Reproduction.objects.create(
            femelle=femelle,
            male=male,
            accouplement=instance,
        )
        return

    # Maj si la Reproduction existe déjà, sinon créer.
    try:
        repro = instance.reproduction  # reverse OneToOne depuis Reproduction.accouplement
    except Reproduction.DoesNotExist:
        Reproduction.objects.create(
            femelle=femelle,
            male=male,
            accouplement=instance,
        )
    else:
        updated = False
        if repro.femelle_id != (femelle.id if femelle else None):
            repro.femelle = femelle
            updated = True
        if repro.male_id != (male.id if male else None):
            repro.male = male
            updated = True
        if updated:
            repro.save(update_fields=["femelle", "male", "date_mise_a_jour"])


@receiver(post_save, sender=Gestation)
def attach_gestation_to_reproduction(sender, instance, **kwargs):
    """
    Associe la Gestation au cycle Reproduction de la femelle concernée.
    On prend la reproduction la plus récente pour cette femelle.
    """
    repro = (
        Reproduction.objects
        .filter(femelle=instance.boucle_brebis)
        .order_by('-accouplement__date_debut_lutte', '-date_creation')
        .first()
    )
    if repro and repro.gestation_id != instance.id:
        repro.gestation = instance
        repro.save(update_fields=["gestation", "date_mise_a_jour"])


@receiver(post_save, sender=Naissance)
def attach_naissance_to_reproduction(sender, instance, **kwargs):
    """
    Associe la Naissance au cycle Reproduction de la femelle concernée.
    On prend la reproduction la plus récente pour cette femelle.
    """
    repro = (
        Reproduction.objects
        .filter(femelle=instance.boucle_mere)
        .order_by('-accouplement__date_debut_lutte', '-date_creation')
        .first()
    )
    if repro and repro.naissance_id != instance.id:
        repro.naissance = instance
        repro.save(update_fields=["naissance", "date_mise_a_jour"])


@receiver(pre_delete, sender=Accouplement)
def delete_reproduction_with_accouplement(sender, instance, **kwargs):
    """
    Supprime explicitement la Reproduction liée quand un Accouplement est supprimé.
    NOTE : Si Reproduction.accouplement a on_delete=CASCADE, ceci est redondant
    (mais inoffensif).
    """
    try:
        repro = instance.reproduction
    except Reproduction.DoesNotExist:
        return
    repro.delete()

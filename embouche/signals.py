# accouplement/signals.py
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Embouche

@receiver(pre_save, sender=Embouche)
def calculer_duree_et_poids_engraissement(sender, instance: Embouche, **kwargs):
    """
    Calcule automatiquement:
      - duree (en jours) si date_fin présente (sinon None)
      - poids_engraissement = poids_fin - poids_initial (sinon None)
    Laisse la validation métier au modèle (clean()).
    """
    # Durée
    if instance.date_entree and instance.date_fin:
        instance.duree = (instance.date_fin - instance.date_entree).days
    else:
        instance.duree = None

    # Poids d'engraissement
    if instance.poids_initial is not None and instance.poids_fin is not None:
        instance.poids_engraissement = instance.poids_fin - instance.poids_initial
    else:
        instance.poids_engraissement = None

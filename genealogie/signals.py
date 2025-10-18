# genealogie/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Genealogie


@receiver(post_save, sender=Genealogie)
def calculer_fa_automatiquement(sender, instance: Genealogie, created, **kwargs):
    """
    Après chaque sauvegarde de Genealogie, calcule le coefficient de consanguinité (en %)
    via la propriété `coefficient_consanguinite` et le stocke dans le champ `fa`.

    - On compare avant d’écrire pour éviter les écritures inutiles.
    - On utilise QuerySet.update(...) pour ne PAS redéclencher post_save.
    """
    try:
        nouveau_fa = float(instance.coefficient_consanguinite)  # pourcentage (0..100)
    except Exception:
        # En cas de souci (parents manquants, etc.), ne bloque pas la sauvegarde.
        return

    ancien_fa = float(instance.fa or 0.0)

    # Tolérance pour éviter les micro-différences d'arrondi
    if abs(nouveau_fa - ancien_fa) > 1e-6:
        Genealogie.objects.filter(pk=instance.pk).update(fa=nouveau_fa)

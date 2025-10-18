# alimentation/signals.py
from datetime import datetime as _dt

from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Alimentation


@receiver(pre_save, sender=Alimentation, dispatch_uid="alimentation_pre_save_validate")
def validate_alimentation(sender, instance: Alimentation, **kwargs):
    """
    Validation avant sauvegarde :
    - Date non future
    - Quantité > 0
    - Pas de doublon (Boucle_Ovin + Date_alimentation)
    """
    errors = {}

    # --- Date (autorise None ; "required" géré par le form)
    today = getattr(timezone, "localdate", lambda: timezone.now().date())()
    d = instance.Date_alimentation
    # Par sûreté: si on reçoit un datetime (rare avec DateField), on le convertit
    if isinstance(d, _dt):
        d = d.date()

    if d and d > today:
        errors["Date_alimentation"] = "La date ne peut pas être dans le futur."

    # --- Quantité (autorise None)
    if instance.Quantite_Kg is not None and instance.Quantite_Kg <= 0:
        errors["Quantite_Kg"] = "La quantité doit être supérieure à zéro."

    # --- Doublon (Boucle_Ovin + Date_alimentation)
    if instance.Boucle_Ovin_id and d:
        exists = (
            Alimentation.objects
            .filter(Boucle_Ovin_id=instance.Boucle_Ovin_id, Date_alimentation=d)
            .exclude(pk=instance.pk)
            .exists()
        )
        if exists:
            errors["Date_alimentation"] = (
                "Un enregistrement d’alimentation existe déjà pour cet ovin à cette date."
            )

    if errors:
        raise ValidationError(errors)

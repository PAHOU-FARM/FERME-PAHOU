# historiquetroupeau/signals.py
from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from django.db import transaction

from troupeau.models import Troupeau
from .models import Historiquetroupeau


# === PRE-SAVE : mémorise l'ancien état pour comparaison ===
@receiver(pre_save, sender=Troupeau)
def _save_old_instance(sender, instance, **kwargs):
    """
    Avant la sauvegarde d'un Troupeau, stocke son ancien état dans instance._old_instance
    pour comparer en post_save.
    """
    if instance.pk:
        try:
            instance._old_instance = Troupeau.objects.get(pk=instance.pk)
        except Troupeau.DoesNotExist:
            instance._old_instance = None
    else:
        instance._old_instance = None


# === POST-SAVE : création/modification ===
@receiver(post_save, sender=Troupeau)
def _create_historique_after_save(sender, instance, created, **kwargs):
    """
    Crée une ligne d'historique après sauvegarde :
    - 'Création' si nouvel objet
    - 'Modification' si au moins un champ suivi a changé
    """
    mapping = [
        ("boucle_ovin", "ancienne_boucle", "nouvelle_boucle"),
        ("naissance_date", "ancienne_naissance_date", "nouvelle_naissance_date"),
        ("boucle_active", "ancienne_boucle_active", "nouvelle_boucle_active"),
        ("proprietaire_ovin", "ancien_proprietaire", "nouveau_proprietaire"),
        ("origine_ovin", "ancienne_origine", "nouvelle_origine"),
        ("statut", "ancien_statut", "nouveau_statut"),
        ("sexe", "ancien_sexe", "nouveau_sexe"),
        ("race", "ancienne_race", "nouvelle_race"),
        ("achat_date", "ancienne_achat_date", "nouvelle_achat_date"),
        ("entree_date", "ancienne_entree_date", "nouvelle_entree_date"),
        ("date_sortie", "ancienne_date_sortie", "nouvelle_date_sortie"),
    ]

    def _event_date_creation():
        return (
            instance.naissance_date
            or instance.entree_date
            or instance.achat_date
            or instance.date_sortie
            or timezone.now().date()
        )

    def _event_date_update():
        return (
            instance.entree_date
            or instance.achat_date
            or instance.date_sortie
            or timezone.now().date()
        )

    if created:
        data = {
            "troupeau": instance,
            "date_evenement": _event_date_creation(),
            "statut": "Création",
            "observations": "Création du troupeau",
        }
        for field, _old_field, new_field in mapping:
            data[new_field] = getattr(instance, field, None)
        Historiquetroupeau.objects.create(**data)
        _cleanup_history(instance)  # optionnel
        return

    old = getattr(instance, "_old_instance", None)
    if not old:
        return

    changements = {}
    for field, old_field, new_field in mapping:
        old_val = getattr(old, field, None)
        new_val = getattr(instance, field, None)
        if _values_different(old_val, new_val):
            changements[old_field] = old_val
            changements[new_field] = new_val

    if changements:
        data = {
            "troupeau": instance,
            "date_evenement": _event_date_update(),
            "statut": "Modification",
            "observations": "Modification du troupeau",
        }
        data.update(changements)
        Historiquetroupeau.objects.create(**data)
        _cleanup_history(instance)  # optionnel


# === PRE-DELETE : suppression ===
@receiver(pre_delete, sender=Troupeau)
def _create_historique_before_delete(sender, instance, **kwargs):
    """
    Avant suppression, créer une ligne d'historique 'Suppression'.
    La FK de Historiquetroupeau est SET_NULL, donc on met troupeau=None.
    """
    with transaction.atomic():
        Historiquetroupeau.objects.create(
            troupeau=None,
            date_evenement=timezone.now().date(),
            statut="Suppression",
            observations=f"Animal supprimé: {getattr(instance, 'boucle_ovin', '—')}",
            ancienne_boucle=getattr(instance, 'boucle_ovin', None),
            ancienne_naissance_date=getattr(instance, 'naissance_date', None),
            ancienne_boucle_active=getattr(instance, 'boucle_active', None),
            ancien_proprietaire=getattr(instance, 'proprietaire_ovin', None),
            ancienne_origine=getattr(instance, 'origine_ovin', None),
            ancien_statut=getattr(instance, 'statut', None),
            ancien_sexe=getattr(instance, 'sexe', None),
            ancienne_race=getattr(instance, 'race', None),
            ancienne_achat_date=getattr(instance, 'achat_date', None),
            ancienne_entree_date=getattr(instance, 'entree_date', None),
            ancienne_date_sortie=getattr(instance, 'date_sortie', None),
        )


# === Utils ===

def _values_different(a, b):
    if a is None and b is None:
        return False
    if (a is None) != (b is None):
        return True
    if isinstance(a, float) and isinstance(b, float):
        return abs(a - b) > 1e-9
    return a != b


def _cleanup_history(instance, keep=100):
    """
    Optionnel : garde uniquement les 'keep' derniers historiques pour un animal,
    pour éviter l’accumulation infinie.
    """
    try:
        ids_to_delete = list(
            Historiquetroupeau.objects
            .filter(troupeau=instance)
            .order_by('-date_evenement', '-id')
            .values_list('id', flat=True)[keep:]
        )
        if ids_to_delete:
            Historiquetroupeau.objects.filter(id__in=ids_to_delete).delete()
    except Exception:
        # on évite toute propagation d’erreur depuis un nettoyage
        pass

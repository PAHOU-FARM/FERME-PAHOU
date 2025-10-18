from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
import logging

from .models import Troupeau
from historiquetroupeau.models import Historiquetroupeau

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Troupeau, dispatch_uid="troupeau_pre_save_historique_modification")
def creer_historique_modification(sender, instance, **kwargs):
    """
    Crée un historique lors de la modification d'un troupeau.
    """
    # Si création, rien à faire ici
    if not instance.pk:
        return

    try:
        # On lit l'ancien état tel qu'en BD
        ancien = Troupeau.objects.get(pk=instance.pk)
    except ObjectDoesNotExist:
        logger.warning(f"Tentative de modification d'un Troupeau inexistant: {instance.pk}")
        return

    # Champs à suivre (cohérents avec le modèle)
    champs_a_suivre = [
        'boucle_ovin',
        'naissance_date',
        'boucle_active',
        'proprietaire_ovin',
        'origine_ovin',
        'statut',
        'sexe',
        'race',
        'achat_date',
        'entree_date',
        'date_sortie',
        'poids_initial',
        'taille_initiale',
        'coefficient_consanguinite',
    ]

    # Mapping vers les champs du modèle d'historique
    correspondance_champs = {
        'boucle_ovin': ('ancienne_boucle', 'nouvelle_boucle'),
        'naissance_date': ('ancienne_naissance_date', 'nouvelle_naissance_date'),
        'boucle_active': ('ancienne_boucle_active', 'nouvelle_boucle_active'),
        'proprietaire_ovin': ('ancien_proprietaire', 'nouveau_proprietaire'),
        'origine_ovin': ('ancienne_origine', 'nouvelle_origine'),
        'statut': ('ancien_statut', 'nouveau_statut'),
        'sexe': ('ancien_sexe', 'nouveau_sexe'),
        'race': ('ancienne_race', 'nouvelle_race'),
        'achat_date': ('ancienne_achat_date', 'nouvelle_achat_date'),
        'entree_date': ('ancienne_entree_date', 'nouvelle_entree_date'),
        'date_sortie': ('ancienne_date_sortie', 'nouvelle_date_sortie'),
        'poids_initial': ('ancien_poids_initial', 'nouveau_poids_initial'),
        'taille_initiale': ('ancienne_taille_initiale', 'nouvelle_taille_initiale'),
        'coefficient_consanguinite': ('ancien_coefficient', 'nouveau_coefficient'),
    }

    changements = []
    donnees_historique = {}
    changements_details = []

    for champ in champs_a_suivre:
        if not hasattr(ancien, champ) or not hasattr(instance, champ):
            logger.warning(f"Champ {champ} non trouvé sur Troupeau")
            continue

        try:
            ancien_val = getattr(ancien, champ)
            nouveau_val = getattr(instance, champ)

            if _valeurs_different(ancien_val, nouveau_val):
                changements.append(champ)

                ancien_str = _formater_valeur(ancien_val)
                nouveau_str = _formater_valeur(nouveau_val)
                changements_details.append(f"{champ}: {ancien_str} → {nouveau_str}")

                if champ in correspondance_champs:
                    ancien_nom, nouveau_nom = correspondance_champs[champ]
                    donnees_historique[ancien_nom] = ancien_val
                    donnees_historique[nouveau_nom] = nouveau_val

        except (AttributeError, TypeError) as e:
            logger.error(f"Erreur comparaison champ {champ}: {e}")
            continue

    if changements:
        try:
            with transaction.atomic():
                observations = f"Champs modifiés: {', '.join(changements)}"
                if changements_details:
                    details = '; '.join(changements_details[:3])
                    observations += f"\nDétails: {details}"
                    if len(changements_details) > 3:
                        observations += f" (+{len(changements_details) - 3} autres)"

                Historiquetroupeau.objects.create(
                    troupeau=instance,
                    date_evenement=timezone.now().date(),
                    statut='Modification',
                    observations=observations[:500],
                    **donnees_historique
                )
                logger.info(f"Historique créé pour Troupeau {instance.pk}: {len(changements)} champ(s) modifié(s)")
        except Exception as e:
            logger.error(f"Erreur création historique (modification) pour {instance.pk}: {e}")


@receiver(post_save, sender=Troupeau, dispatch_uid="troupeau_post_save_historique_creation")
def creer_historique_creation(sender, instance, created, **kwargs):
    """
    Crée un historique lors de la création d'un nouvel animal.
    """
    if not created:
        return

    try:
        with transaction.atomic():
            # Évite l'avertissement IDE sur get_FOO_display (même rendu)
            sexe_label = dict(Troupeau.SEXE_CHOIX).get(instance.sexe, instance.sexe)
            race_label = dict(Troupeau.RACE_CHOIX).get(instance.race, instance.race)

            Historiquetroupeau.objects.create(
                troupeau=instance,
                date_evenement=timezone.now().date(),
                statut='Création',
                observations=f"Nouvel animal ajouté: {instance.boucle_ovin} ({sexe_label}, {race_label})",
                nouvelle_boucle=instance.boucle_ovin,
                nouvelle_naissance_date=instance.naissance_date,
                nouveau_sexe=instance.sexe,
                nouvelle_race=instance.race,
                nouveau_statut=instance.statut,
                nouveau_proprietaire=instance.proprietaire_ovin,
                nouvelle_origine=instance.origine_ovin,
            )
            logger.info(f"Historique de création créé pour Troupeau {instance.pk}")
    except Exception as e:
        logger.error(f"Erreur historique de création pour {instance.pk}: {e}")


@receiver(pre_delete, sender=Troupeau, dispatch_uid="troupeau_pre_delete_historique_suppression")
def creer_historique_suppression(sender, instance, **kwargs):
    """
    Crée un historique avant la suppression d'un animal.
    """
    try:
        with transaction.atomic():
            sexe_label = dict(Troupeau.SEXE_CHOIX).get(instance.sexe, instance.sexe)
            race_label = dict(Troupeau.RACE_CHOIX).get(instance.race, instance.race)

            Historiquetroupeau.objects.create(
                troupeau=None,  # L'objet va être supprimé
                date_evenement=timezone.now().date(),
                statut='Suppression',
                observations=f"Animal supprimé: {instance.boucle_ovin} ({sexe_label}, {race_label})",
                ancienne_boucle=instance.boucle_ovin,
                ancienne_naissance_date=instance.naissance_date,
                ancien_sexe=instance.sexe,
                ancienne_race=instance.race,
                ancien_statut=instance.statut,
                ancien_proprietaire=instance.proprietaire_ovin,
                ancienne_origine=instance.origine_ovin,
            )
            logger.info(f"Historique de suppression créé pour Troupeau {instance.pk}")
    except Exception as e:
        logger.error(f"Erreur historique de suppression pour {instance.pk}: {e}")


def _valeurs_different(val1, val2):
    """
    Compare deux valeurs en gérant les cas particuliers (None, float, etc.)
    """
    if val1 is None and val2 is None:
        return False
    if (val1 is None) != (val2 is None):
        return True
    if isinstance(val1, float) and isinstance(val2, float):
        return abs(val1 - val2) > 0.00001
    return val1 != val2


def _formater_valeur(valeur):
    """
    Formate une valeur pour l'affichage dans l'historique
    """
    if valeur is None:
        return "Non défini"
    if isinstance(valeur, bool):
        return "Oui" if valeur else "Non"
    if isinstance(valeur, float):
        return f"{valeur:.2f}"
    if hasattr(valeur, 'strftime'):  # Date/DateTime
        return valeur.strftime("%d/%m/%Y")
    return str(valeur)


@receiver(post_save, sender=Troupeau, dispatch_uid="troupeau_post_save_nettoyage_historique")
def nettoyer_historique_ancien(sender, instance, **kwargs):
    """
    Garde les 100 derniers enregistrements d'historique par animal.
    """
    try:
        anciens = (Historiquetroupeau.objects
                   .filter(troupeau=instance)
                   .order_by('-date_evenement')
                   [100:])  # tout ce qui dépasse 100
        if anciens:
            ids = list(anciens.values_list('id', flat=True))
            Historiquetroupeau.objects.filter(id__in=ids).delete()
            logger.info(f"Nettoyage historique: {len(ids)} enregistrements supprimés pour {instance.pk}")
    except Exception as e:
        logger.error(f"Erreur nettoyage historique pour {instance.pk}: {e}")


class DisableSignals:
    """
    Context manager pour désactiver temporairement les signaux.
    Usage:
      with DisableSignals():
          Troupeau.objects.bulk_create([...])
    """

    def __init__(self):
        self.receivers = []

    def __enter__(self):
        # Déconnecte proprement uniquement ceux existants
        to_disable = [
            (pre_save, creer_historique_modification),
            (post_save, creer_historique_creation),
            (pre_delete, creer_historique_suppression),
            (post_save, nettoyer_historique_ancien),
        ]
        for signal, receiver_func in to_disable:
            try:
                signal.disconnect(receiver_func, sender=Troupeau)
                self.receivers.append((signal, receiver_func))
            except Exception:
                pass
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for signal, receiver_func in self.receivers:
            signal.connect(receiver_func, sender=Troupeau)

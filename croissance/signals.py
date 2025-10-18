from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import Croissance


@receiver(pre_save, sender=Croissance)
def log_croissance_changes(sender, instance: Croissance, **kwargs):
    """
    Avant la sauvegarde d'une mesure 'courante' (est_historique=False),
    si Poids/Taille (ou état/évaluation) changent, on conserve un snapshot
    'historique' (est_historique=True) de l'ancienne valeur pour CE couple
    (Boucle_Ovin, Date_mesure). On utilise get_or_create pour respecter
    la contrainte unique_together et on met à jour l'historique si déjà présent.
    """
    # 1) Pas d'historisation pour une première création ni pour une ligne historique
    if not instance.pk or instance.est_historique:
        return

    # 2) Récupérer l'état précédent pour comparer
    try:
        previous = Croissance.objects.get(pk=instance.pk)
    except Croissance.DoesNotExist:
        return

    # 3) Déterminer si quelque chose de pertinent a changé
    changed = any([
        previous.Poids_Kg != instance.Poids_Kg,
        previous.Taille_CM != instance.Taille_CM,
        previous.Etat_Sante != instance.Etat_Sante,
        previous.Croissance_Evaluation != instance.Croissance_Evaluation,
    ])
    if not changed:
        return

    # 4) Créer/mettre à jour l'entrée historique unique pour (Boucle_Ovin, Date_mesure, True)
    hist, created = Croissance.objects.get_or_create(
        Boucle_Ovin=instance.Boucle_Ovin,
        Date_mesure=previous.Date_mesure,
        est_historique=True,
        defaults={
            'Poids_Kg': previous.Poids_Kg,
            'Taille_CM': previous.Taille_CM,
            'Etat_Sante': previous.Etat_Sante,
            'Croissance_Evaluation': previous.Croissance_Evaluation,
            'Age_en_Mois': previous.Age_en_Mois,
            'Observations': previous.Observations,
        }
    )

    if not created:
        # On écrase le snapshot pour refléter la dernière "ancienne" valeur
        Croissance.objects.filter(pk=hist.pk).update(
            Poids_Kg=previous.Poids_Kg,
            Taille_CM=previous.Taille_CM,
            Etat_Sante=previous.Etat_Sante,
            Croissance_Evaluation=previous.Croissance_Evaluation,
            Age_en_Mois=previous.Age_en_Mois,
            Observations=previous.Observations,
        )

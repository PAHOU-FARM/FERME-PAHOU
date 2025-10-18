# historiquetroupeau/models.py
from django.db import models


class Historiquetroupeau(models.Model):
    """
    Historique des changements/événements concernant un animal du troupeau.
    """

    STATUT_CHOIX = [
        # Evénements système (utilisés par les signaux)
        ('Création', 'Création'),
        ('Modification', 'Modification'),
        ('Suppression', 'Suppression'),

        # Evénements métier possibles
        ('Naissance', 'Naissance'),
        ('Vendu', 'Vendu'),
        ('Décédé', 'Décédé'),
        ('Sortie', 'Sortie'),
        ('Prêt notre ferme', 'Prêt notre ferme'),
        ('Prêt autre ferme', 'Prêt autre ferme'),
        ('Échange Ovin', 'Échange Ovin'),
        ('Achat', 'Achat'),
        ('Soin', 'Soin'),
    ]

    # Référence souple (pas d'import direct pour éviter les imports circulaires)
    troupeau = models.ForeignKey(
        'troupeau.Troupeau',
        on_delete=models.SET_NULL,       # autorise None si l'animal est supprimé
        null=True,
        blank=True,
        related_name='historiques'
    )

    date_evenement = models.DateField()
    statut = models.CharField(max_length=30, choices=STATUT_CHOIX)

    # Anciennes valeurs
    ancienne_boucle = models.CharField(max_length=20, blank=True, null=True)
    ancienne_naissance_date = models.DateField(blank=True, null=True)
    ancienne_boucle_active = models.BooleanField(blank=True, null=True)
    ancien_proprietaire = models.CharField(max_length=50, blank=True, null=True)
    ancienne_origine = models.CharField(max_length=50, blank=True, null=True)
    ancien_statut = models.CharField(max_length=30, blank=True, null=True)
    ancien_sexe = models.CharField(max_length=10, blank=True, null=True)
    ancienne_race = models.CharField(max_length=50, blank=True, null=True)
    ancienne_achat_date = models.DateField(blank=True, null=True)
    ancienne_entree_date = models.DateField(blank=True, null=True)
    ancienne_date_sortie = models.DateField(blank=True, null=True)

    # Nouvelles valeurs
    nouvelle_boucle = models.CharField(max_length=20, blank=True, null=True)
    nouvelle_naissance_date = models.DateField(blank=True, null=True)
    nouvelle_boucle_active = models.BooleanField(blank=True, null=True)
    nouveau_proprietaire = models.CharField(max_length=50, blank=True, null=True)
    nouvelle_origine = models.CharField(max_length=50, blank=True, null=True)
    nouveau_statut = models.CharField(max_length=30, blank=True, null=True)
    nouveau_sexe = models.CharField(max_length=10, blank=True, null=True)
    nouvelle_race = models.CharField(max_length=50, blank=True, null=True)
    nouvelle_achat_date = models.DateField(blank=True, null=True)
    nouvelle_entree_date = models.DateField(blank=True, null=True)
    nouvelle_date_sortie = models.DateField(blank=True, null=True)

    observations = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Historique du Troupeau"
        verbose_name_plural = "Historique des Troupeaux"
        ordering = ['-date_evenement']
        db_table = 'historiquetroupeau'
        indexes = [
            models.Index(fields=['troupeau']),
            models.Index(fields=['date_evenement']),
            models.Index(fields=['statut']),
        ]

    def __str__(self):
        boucle = (
            self.troupeau.boucle_ovin
            if self.troupeau else
            (self.nouvelle_boucle or self.ancienne_boucle or "?")
        )
        return f"📍 {boucle} - {self.statut} ({self.date_evenement})"

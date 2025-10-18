from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

# Pas d'import direct de Troupeau pour éviter les soucis d'import circulaire
# On référence la FK sous forme de chaîne : 'troupeau.Troupeau'

ETAT_CHOICES = [
    ('Bon', 'Bon'),
    ('Moyen', 'Moyen'),
    ('Mauvais', 'Mauvais'),
    ('Malade', 'Malade'),
]

EVALUATION_CHOICES = [
    ('Normale', 'Normale'),
    ('Retard de croissance', 'Retard de croissance'),
    ('Croissance accélérée', 'Croissance accélérée'),
]


class Croissance(models.Model):
    Boucle_Ovin = models.ForeignKey(
        'troupeau.Troupeau',
        on_delete=models.CASCADE,
        related_name='croissances'  # optionnel mais pratique
    )
    Date_mesure = models.DateField()
    Poids_Kg = models.FloatField()
    Taille_CM = models.FloatField()
    Etat_Sante = models.CharField(choices=ETAT_CHOICES, max_length=20)
    Croissance_Evaluation = models.CharField(choices=EVALUATION_CHOICES, max_length=30, null=True, blank=True)
    Age_en_Mois = models.PositiveIntegerField(null=True, blank=True)
    Observations = models.TextField(blank=True)
    est_historique = models.BooleanField(default=False)

    class Meta:
        unique_together = ('Boucle_Ovin', 'Date_mesure', 'est_historique')
        ordering = ['-Date_mesure']
        verbose_name = "Suivi de croissance"
        verbose_name_plural = "Suivis de croissance"

    def __str__(self):
        boucle = getattr(self.Boucle_Ovin, 'boucle_ovin', self.Boucle_Ovin_id)
        return f"Croissance {boucle} — {self.Date_mesure}"

    def clean(self):
        """
        Validations métier, en restant compatible avec les noms de champs existants.
        """
        # Date requise
        if not self.Date_mesure:
            raise ValidationError("La date de mesure est obligatoire.")

        today = timezone.localdate()
        if self.Date_mesure > today:
            raise ValidationError("La date de mesure ne peut pas être dans le futur.")

        # Récupère les champs du modèle Troupeau avec leurs vrais noms (snake_case)
        naissance = getattr(self.Boucle_Ovin, 'naissance_date', None)
        actif = getattr(self.Boucle_Ovin, 'boucle_active', True)

        if naissance:
            if self.Date_mesure < naissance:
                raise ValidationError("La date de mesure ne peut pas être antérieure à la naissance de l’animal.")
        else:
            # Si la date de naissance n'est pas renseignée, on ne peut pas valider certains contrôles
            # On laisse passer mais on n'applique pas les règles liées à l'âge.
            pass

        if not actif:
            raise ValidationError("Impossible d'ajouter un suivi de croissance pour un animal inactif.")

        # Valeurs positives
        if self.Poids_Kg is None or self.Poids_Kg <= 0:
            raise ValidationError("Le poids doit être strictement positif.")
        if self.Taille_CM is None or self.Taille_CM <= 0:
            raise ValidationError("La taille doit être strictement positive.")

        # Règles simples selon l’âge si date de naissance connue
        if naissance:
            age = (self.Date_mesure - naissance).days // 30
            if age < 3 and self.Poids_Kg < 6:
                raise ValidationError("Poids trop faible pour un agneau de moins de 3 mois.")
            if age >= 12 and self.Poids_Kg < 30:
                raise ValidationError("Poids insuffisant pour un ovin d’au moins 12 mois.")

    def save(self, *args, **kwargs):
        """
        Calcule Age_en_Mois et Croissance_Evaluation automatiquement si possible,
        puis sauvegarde.
        """
        # Calcule l'âge en mois si la naissance est connue
        naissance = getattr(self.Boucle_Ovin, 'naissance_date', None)
        if naissance:
            self.Age_en_Mois = max(0, (self.Date_mesure - naissance).days // 30)
        else:
            self.Age_en_Mois = None

        # Évaluation automatique (seulement si ce n’est pas un enregistrement historique)
        if not self.est_historique and self.Age_en_Mois is not None and self.Poids_Kg is not None:
            age = self.Age_en_Mois
            # Seuils simples (tu peux les affiner selon ta filière)
            if age < 3:
                if self.Poids_Kg < 6:
                    self.Croissance_Evaluation = 'Retard de croissance'
                elif self.Poids_Kg > 8:
                    self.Croissance_Evaluation = 'Croissance accélérée'
                else:
                    self.Croissance_Evaluation = 'Normale'
            elif age >= 12:
                if self.Poids_Kg < 35:
                    self.Croissance_Evaluation = 'Retard de croissance'
                elif self.Poids_Kg > 40:
                    self.Croissance_Evaluation = 'Croissance accélérée'
                else:
                    self.Croissance_Evaluation = 'Normale'
            else:
                self.Croissance_Evaluation = 'Normale'

        # Laisse la validation s’exécuter (levera si incohérence)
        self.full_clean()
        super().save(*args, **kwargs)

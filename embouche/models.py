from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date

from troupeau.models import Troupeau


class Embouche(models.Model):
    boucle_ovin = models.ForeignKey(
        Troupeau,
        on_delete=models.CASCADE,
        related_name='embouches',
        verbose_name="Boucle ovin",
    )

    date_entree = models.DateField(verbose_name="Date d'entrée")
    poids_initial = models.FloatField(verbose_name="Poids initial (kg)")
    date_fin = models.DateField(null=True, blank=True, verbose_name="Date de fin")
    poids_fin = models.FloatField(null=True, blank=True, verbose_name="Poids final (kg)")
    duree = models.PositiveIntegerField(null=True, blank=True, verbose_name="Durée (jours)")
    poids_engraissement = models.FloatField(null=True, blank=True, verbose_name="Poids d'engraissement (kg)")

    # Aligne les choix avec le modèle Troupeau
    proprietaire = models.CharField(
        choices=Troupeau.PROPRIETAIRE_CHOIX,  # ex: ('miguel','Miguel'), ('virgile','Virgile')
        max_length=20,
        verbose_name="Propriétaire",
    )

    sexe = models.CharField(
        choices=Troupeau.SEXE_CHOIX,  # ('male','Mâle'), ('femelle','Femelle')
        max_length=10,
        verbose_name="Sexe",
    )

    observations = models.TextField(blank=True, verbose_name="Observations")

    class Meta:
        verbose_name = "Embouche"
        verbose_name_plural = "Embouches"
        constraints = [
            models.UniqueConstraint(fields=['boucle_ovin', 'date_entree'], name='unique_boucle_date')
        ]
        indexes = [
            models.Index(fields=['boucle_ovin'])
        ]
        ordering = ['-date_entree', '-id']

    def __str__(self):
        boucle = getattr(self.boucle_ovin, 'boucle_ovin', self.boucle_ovin_id)
        return f"Embouche — {boucle} (entrée: {self.date_entree})"

    @property
    def age(self):
        """
        Âge en mois de l'ovin au moment de l'entrée en embouche (approximation 30 j/mois).
        """
        if not self.boucle_ovin or not self.boucle_ovin.naissance_date or not self.date_entree:
            return None
        delta = self.date_entree - self.boucle_ovin.naissance_date
        return max(0, delta.days // 30)

    def clean(self):
        super().clean()
        errors = {}

        # Cohérence de base
        if self.poids_initial is not None and self.poids_initial <= 0:
            errors['poids_initial'] = "Le poids initial doit être strictement positif."
        if self.poids_fin is not None and self.poids_fin <= 0:
            errors['poids_fin'] = "Le poids final doit être strictement positif."

        # Date entrée non future
        if self.date_entree and self.date_entree > timezone.localdate():
            errors['date_entree'] = "La date d'entrée ne peut pas être dans le futur."

        # Doit être postérieure à la naissance
        if self.boucle_ovin and self.boucle_ovin.naissance_date and self.date_entree:
            if self.date_entree < self.boucle_ovin.naissance_date:
                errors['date_entree'] = "La date d'entrée ne peut pas être antérieure à la naissance de l'animal."

        # Âge minimal 6 mois à l'entrée
        if self.age is not None and self.age < 6:
            errors['date_entree'] = "L'ovin doit avoir au moins 6 mois pour entrer en embouche."

        # Fin > entrée
        if self.date_fin and self.date_entree and self.date_fin <= self.date_entree:
            errors['date_fin'] = "La date de fin doit être postérieure à la date d'entrée."

        # Poids final > initial si renseignés
        if self.poids_fin is not None and self.poids_initial is not None:
            if self.poids_fin <= self.poids_initial:
                errors['poids_fin'] = "Le poids final doit être supérieur au poids initial."

        # Durée cohérente si fournie
        if self.date_entree and self.date_fin:
            duree_calc = (self.date_fin - self.date_entree).days
            if self.duree is not None and self.duree != duree_calc:
                errors['duree'] = "La durée ne correspond pas à la différence entre les dates."

        # Poids d'engraissement cohérent si fourni
        if self.poids_initial is not None and self.poids_fin is not None:
            poids_calc = self.poids_fin - self.poids_initial
            if self.poids_engraissement is not None and abs(self.poids_engraissement - poids_calc) > 0.1:
                errors['poids_engraissement'] = "Le poids d'engraissement ne correspond pas à (poids final - poids initial)."

        # Sexe/propriétaire en cohérence (optionnel mais utile)
        if self.boucle_ovin:
            if self.sexe and self.sexe != self.boucle_ovin.sexe:
                errors['sexe'] = "Le sexe ne correspond pas à celui de l'animal sélectionné."
            if self.proprietaire and self.proprietaire != self.boucle_ovin.proprietaire_ovin:
                errors['proprietaire'] = "Le propriétaire ne correspond pas à celui de l'animal sélectionné."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Calcul auto durée
        if self.date_entree and self.date_fin:
            self.duree = (self.date_fin - self.date_entree).days
        else:
            self.duree = None

        # Calcul auto poids d'engraissement
        if self.poids_initial is not None and self.poids_fin is not None:
            self.poids_engraissement = self.poids_fin - self.poids_initial
        else:
            self.poids_engraissement = None

        super().save(*args, **kwargs)

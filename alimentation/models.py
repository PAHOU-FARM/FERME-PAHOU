from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Alimentation(models.Model):
    # ✅ On conserve les mêmes valeurs (clé = libellé) pour ne rien casser
    TYPE_ALIMENT_CHOICES = [
        ('Fourrage', 'Fourrage'),
        ('Foin', 'Foin'),
        ('Tourteau', 'Tourteau'),
        ('Son de mais', 'Son de maïs'),     # libellé plus joli, clé inchangée
        ('Concentré', 'Concentré'),
        ('Complément', 'Complément'),
        ('Eau', 'Eau'),
        ('Autre', 'Autre'),
    ]

    OBJECTIF_CHOICES = [
        ('Entretien', 'Entretien'),
        ('Gestation', 'Gestation'),
        ('Lactation', 'Lactation'),
        ('Croissance', 'Croissance'),
        ('Maladie', 'Maladie'),
        ('Autre', 'Autre'),
    ]

    id = models.AutoField(primary_key=True)

    # ✅ Référence paresseuse vers l'app troupeau (pas d'import direct)
    Boucle_Ovin = models.ForeignKey(
        'troupeau.Troupeau',
        on_delete=models.CASCADE,
        related_name='alimentations',
        verbose_name=_("Animal (boucle)")
    )

    Date_alimentation = models.DateField(
        verbose_name=_("Date d'alimentation"),
        help_text=_("Jour où la ration a été donnée."),
        db_index=True,                       # 🔎 utile pour les listes/rapports
    )
    Type_Aliment = models.CharField(
        max_length=20,
        choices=TYPE_ALIMENT_CHOICES,
        verbose_name=_("Type d'aliment")
    )
    Quantite_Kg = models.FloatField(
        verbose_name=_("Quantité (kg)"),
        help_text=_("Quantité totale distribuée ce jour-là (en kilogrammes).")
    )
    Objectif = models.CharField(
        max_length=20,
        choices=OBJECTIF_CHOICES,
        verbose_name=_("Objectif")
    )
    Observations = models.TextField(
        blank=True,
        default='',
        verbose_name=_("Observations")
    )

    class Meta:
        # 🔒 Un enregistrement par jour et par animal
        constraints = [
            models.UniqueConstraint(
                fields=['Boucle_Ovin', 'Date_alimentation'],
                name='unique_alimentation_per_day'
            ),
        ]
        # 🔎 Index pratique pour filtrer par animal (unique crée déjà un index composé)
        indexes = [
            models.Index(fields=['Boucle_Ovin'], name='idx_alimentation_boucle'),
        ]
        # 🎯 Ordre par défaut (du plus récent au plus ancien)
        ordering = ['-Date_alimentation', '-id']
        verbose_name = "Alimentation"
        verbose_name_plural = "Alimentations"

    def clean(self):
        """
        Garde-fous légers (cohérents et non-cassants) :
        - pas de date future
        - quantité > 0
        - (optionnel, non bloquant si naissance inconnue) : avertir si date avant naissance
        """
        if self.Date_alimentation and self.Date_alimentation > timezone.now().date():
            raise ValidationError("La date ne peut pas être dans le futur.")

        if self.Quantite_Kg is None or self.Quantite_Kg <= 0:
            raise ValidationError("La quantité doit être strictement supérieure à zéro.")

        # ⚠️ Sans bloquer : si la date de naissance est connue, on peut prévenir
        ovin = getattr(self, 'Boucle_Ovin', None)
        if ovin and getattr(ovin, 'naissance_date', None):
            if self.Date_alimentation and self.Date_alimentation < ovin.naissance_date:
                raise ValidationError(
                    "La date d'alimentation ne peut pas précéder la date de naissance de l'animal."
                )

    def __str__(self):
        # Affiche la boucle si dispo, sinon l’ID
        boucle = getattr(self.Boucle_Ovin, 'boucle_ovin', self.Boucle_Ovin_id)
        return f"{boucle} - {self.Date_alimentation}"

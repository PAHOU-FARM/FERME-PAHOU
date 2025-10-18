from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from decimal import Decimal
from datetime import date


class Vente(models.Model):
    TYPE_ACHETEUR_CHOICES = [
        ('Elevage', 'Elevage'),
        ('Abattage', 'Abattage'),
        ('Reproduction', 'Reproduction'),
    ]

    PROPRIETAIRE_CHOICES = [
        ('Virgile', 'Virgile'),
        ('Miguel', 'Miguel'),
    ]

    boucle_ovin = models.ForeignKey(
        'troupeau.Troupeau',
        on_delete=models.CASCADE,
        related_name='ventes',
        verbose_name="Ovin",
    )

    date_vente = models.DateField(verbose_name="Date de vente")

    poids_kg = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Poids (kg)",
    )

    prix_vente = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Prix de vente",
    )

    type_acheteur = models.CharField(
        max_length=20,
        choices=TYPE_ACHETEUR_CHOICES,
        verbose_name="Type d’acheteur",
    )

    proprietaire_ovin = models.CharField(
        max_length=20,
        choices=PROPRIETAIRE_CHOICES,
        verbose_name="Propriétaire",
    )

    observations = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observations",
    )

    class Meta:
        verbose_name = "Vente"
        verbose_name_plural = "Ventes"
        ordering = ['-date_vente']
        indexes = [
            models.Index(fields=['date_vente']),
            models.Index(fields=['type_acheteur']),
            models.Index(fields=['proprietaire_ovin']),
            models.Index(fields=['boucle_ovin']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['boucle_ovin', 'date_vente'],
                name='uniq_vente_ovin_date',
            )
        ]

    def clean(self):
        errors = {}

        if self.poids_kg is not None and self.poids_kg <= 0:
            errors['poids_kg'] = "Le poids doit être strictement supérieur à 0."

        if self.prix_vente is not None and self.prix_vente < 0:
            errors['prix_vente'] = "Le prix doit être supérieur ou égal à 0."

        if self.date_vente and self.date_vente > date.today():
            errors['date_vente'] = "La date de vente ne peut pas être dans le futur."

        if self.type_acheteur and self.type_acheteur not in dict(self.TYPE_ACHETEUR_CHOICES):
            errors['type_acheteur'] = "Type d’acheteur invalide."

        if self.proprietaire_ovin and self.proprietaire_ovin not in dict(self.PROPRIETAIRE_CHOICES):
            errors['proprietaire_ovin'] = "Propriétaire invalide."

        # Facultatif : empêcher la vente d’un ovin inactif (si le champ existe)
        if self.boucle_ovin is not None:
            boucle_active = getattr(self.boucle_ovin, 'boucle_active', True)
            if boucle_active is False:
                errors['boucle_ovin'] = "Cet ovin est inactif et ne peut pas être vendu."

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        num = getattr(self.boucle_ovin, 'boucle_ovin', None)
        ident = num if num is not None else (self.boucle_ovin.pk if self.boucle_ovin else '—')
        date_str = self.date_vente.isoformat() if self.date_vente else '—'
        return f"Vente #{self.pk or '—'} – Ovin {ident} ({date_str})"

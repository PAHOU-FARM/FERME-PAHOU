from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import re

from troupeau.models import Troupeau


class Vaccination(models.Model):
    VOIE_CHOICES = [
        ('Voie sous-cutanée', 'Voie sous-cutanée'),
        ('Voie orale', 'Voie orale'),
        ('Voie intramusculaire', 'Voie intramusculaire'),
        ('Voie intranasale', 'Voie intranasale'),
    ]

    # ✅ FK standard vers la PK de Troupeau (cohérent avec le reste du projet)
    boucle_ovin = models.ForeignKey(
        Troupeau,
        on_delete=models.CASCADE,
        related_name='vaccinations',
        verbose_name="Boucle de l'Ovin",
        help_text="Animal concerné par la vaccination",
    )

    date_vaccination = models.DateField(verbose_name="Date de vaccination")
    type_vaccin = models.CharField(max_length=100, verbose_name="Type de vaccin")
    nom_vaccin = models.CharField(max_length=100, verbose_name="Nom du vaccin")

    # Laisse la validation métier dans clean() pour ne rien casser côté forms/admin
    dose_vaccin = models.FloatField(verbose_name="Dose administrée (mL)")

    voie_administration = models.CharField(
        max_length=30,
        choices=VOIE_CHOICES,
        verbose_name="Voie d'administration"
    )
    nom_veterinaire = models.CharField(max_length=100, verbose_name="Nom du vétérinaire")
    observations = models.TextField(blank=True, null=True, verbose_name="Observations")

    class Meta:
        unique_together = (('boucle_ovin', 'date_vaccination'),)
        ordering = ['-date_vaccination']
        verbose_name = "Vaccination"
        verbose_name_plural = "Vaccinations"
        indexes = [
            models.Index(fields=['boucle_ovin', 'date_vaccination']),
        ]

    def clean(self):
        errors = {}

        # Date non future
        if self.date_vaccination and self.date_vaccination > timezone.localdate():
            errors['date_vaccination'] = "La date de vaccination ne peut pas être dans le futur."

        # Dose positive
        if self.dose_vaccin is None or self.dose_vaccin <= 0:
            errors['dose_vaccin'] = "La dose doit être un nombre positif."

        # Vétérinaire : lettres (avec accents), espaces, tirets, apostrophes
        if self.nom_veterinaire:
            if not re.fullmatch(r"[A-Za-zÀ-ÖØ-öø-ÿ \-']+", self.nom_veterinaire.strip()):
                errors['nom_veterinaire'] = "Le nom du vétérinaire contient des caractères invalides."

        # Type et nom de vaccin non vides après trim
        if self.type_vaccin and not self.type_vaccin.strip():
            errors['type_vaccin'] = "Le type de vaccin est requis."
        if self.nom_vaccin and not self.nom_vaccin.strip():
            errors['nom_vaccin'] = "Le nom du vaccin est requis."

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        # Affiche la boucle si dispo, sinon l’id de la FK
        boucle = getattr(self.boucle_ovin, 'boucle_ovin', self.boucle_ovin_id)
        return f"{boucle} - {self.date_vaccination}"

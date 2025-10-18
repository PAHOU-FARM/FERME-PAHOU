from django.db import models
from django.core.exceptions import ValidationError


class Reproduction(models.Model):
    femelle = models.ForeignKey(
        'troupeau.Troupeau',
        on_delete=models.CASCADE,
        related_name='reproductions_femelle',
        limit_choices_to={'sexe': 'femelle'},
        verbose_name="Femelle",
    )
    male = models.ForeignKey(
        'troupeau.Troupeau',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reproductions_male',
        limit_choices_to={'sexe': 'male'},
        verbose_name="Mâle",
    )

    accouplement = models.OneToOneField(
        'accouplement.Accouplement',
        on_delete=models.CASCADE,
        related_name='reproduction',
        verbose_name="Accouplement",
    )
    gestation = models.OneToOneField(
        'gestation.Gestation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reproduction',
        verbose_name="Gestation",
    )
    naissance = models.OneToOneField(
        'naissance.Naissance',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reproduction',
        verbose_name="Naissance",
    )

    observations = models.TextField(blank=True, verbose_name="Observations")

    date_creation = models.DateTimeField(auto_now_add=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cycle de reproduction"
        verbose_name_plural = "Cycles de reproduction"
        ordering = ['-accouplement__date_debut_lutte']
        indexes = [
            models.Index(fields=['femelle']),
            models.Index(fields=['male']),
        ]

    def __str__(self):
        boucle = getattr(self.femelle, 'boucle_ovin', '—')
        acc_date = getattr(self.accouplement, 'date_debut_lutte', None)
        acc_str = acc_date.strftime('%d/%m/%Y') if acc_date else '—'
        return f"{boucle} — Cycle du {acc_str}"

    def clean(self):
        super().clean()

        # Cohérence avec Accouplement
        if self.accouplement:
            # La femelle doit correspondre à la brebis de l'accouplement
            if self.accouplement.boucle_brebis != self.femelle:
                raise ValidationError("La femelle ne correspond pas à celle de l'accouplement.")

            # Si un mâle est indiqué ici, il doit correspondre au bélier de l'accouplement (s'il existe)
            if self.male and self.accouplement.boucle_belier and self.accouplement.boucle_belier != self.male:
                raise ValidationError("Le mâle ne correspond pas à celui de l'accouplement.")

        # Cohérence avec Gestation
        if self.gestation and self.gestation.boucle_brebis != self.femelle:
            raise ValidationError("La femelle de la gestation ne correspond pas à celle de la reproduction.")

        # Cohérence avec Naissance
        if self.naissance and self.naissance.boucle_mere != self.femelle:
            raise ValidationError("La mère de la naissance ne correspond pas à celle de la reproduction.")

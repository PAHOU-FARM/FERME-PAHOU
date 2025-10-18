from datetime import date
from django.db import models
from django.core.exceptions import ValidationError

from troupeau.models import Troupeau


class Accouplement(models.Model):
    boucle_belier = models.ForeignKey(
        Troupeau,
        on_delete=models.CASCADE,
        related_name='accouplements_comme_belier',
        limit_choices_to={'sexe': 'male', 'boucle_active': True},
        verbose_name="Bélier"
    )
    boucle_brebis = models.ForeignKey(
        Troupeau,
        on_delete=models.CASCADE,
        related_name='accouplements_comme_brebis',
        limit_choices_to={'sexe': 'femelle', 'boucle_active': True},
        verbose_name="Brebis"
    )

    date_debut_lutte = models.DateField(verbose_name="Début de lutte")
    date_fin_lutte = models.DateField(blank=True, null=True, verbose_name="Fin de lutte")
    date_verification_gestation = models.DateField(blank=True, null=True, verbose_name="Vérification gestation")
    date_gestation = models.DateField(blank=True, null=True, verbose_name="Date de gestation")

    observations = models.TextField(blank=True, null=True)
    accouplement_reussi = models.BooleanField(default=False, editable=False)

    class Meta:
        verbose_name = "Accouplement"
        verbose_name_plural = "Accouplements"
        ordering = ['-date_debut_lutte']
        indexes = [
            models.Index(fields=['boucle_brebis']),
            models.Index(fields=['boucle_belier']),
            models.Index(fields=['date_debut_lutte']),
        ]
        # Évite les doublons exacts pour un même couple à une même date
        constraints = [
            models.UniqueConstraint(
                fields=['boucle_belier', 'boucle_brebis', 'date_debut_lutte'],
                name='uniq_couple_debut_lutte',
            )
        ]

    def __str__(self):
        belier = getattr(self.boucle_belier, 'boucle_ovin', '—')
        brebis = getattr(self.boucle_brebis, 'boucle_ovin', '—')
        d = self.date_debut_lutte.strftime('%d/%m/%Y') if self.date_debut_lutte else '—'
        return f"Accouplement ({brebis} × {belier}) – {d}"

    def clean(self):
        super().clean()

        # --- Début obligatoire et pas dans le futur
        if not self.date_debut_lutte:
            raise ValidationError("Vous devez renseigner une date de début de lutte.")
        if self.date_debut_lutte > date.today():
            raise ValidationError("La date de début de lutte ne peut pas être dans le futur.")

        # --- Ordre logique des dates
        if self.date_fin_lutte and self.date_fin_lutte < self.date_debut_lutte:
            raise ValidationError("La fin de lutte ne peut pas précéder le début de lutte.")

        if (self.date_verification_gestation or self.date_gestation) and not self.date_fin_lutte:
            raise ValidationError(
                "Renseignez 'date_fin_lutte' avant la vérification/confirmation de gestation."
            )

        if self.date_verification_gestation and self.date_fin_lutte:
            if self.date_verification_gestation < self.date_fin_lutte:
                raise ValidationError("La date de vérification ne peut pas précéder la fin de lutte.")

        if self.date_gestation and self.date_verification_gestation:
            if self.date_gestation < self.date_verification_gestation:
                raise ValidationError("La date de gestation ne peut pas précéder la vérification.")

        # --- Âges min (basés sur Troupeau.naissance_date)
        def age_en_mois(dn):
            return (self.date_debut_lutte - dn).days / 30.44

        if self.boucle_brebis and self.boucle_brebis.naissance_date:
            age_brebis = age_en_mois(self.boucle_brebis.naissance_date)
            if age_brebis < 10:  # cohérent avec is_reproducteur_age (femelle >= 10 mois)
                raise ValidationError("La brebis doit avoir au moins 10 mois au moment de l'accouplement.")

        if self.boucle_belier and self.boucle_belier.naissance_date:
            age_belier = age_en_mois(self.boucle_belier.naissance_date)
            if age_belier < 8:  # cohérent avec is_reproducteur_age (mâle >= 8 mois)
                raise ValidationError("Le bélier doit avoir au moins 8 mois au moment de l'accouplement.")
            # Optionnel : plafond (ex info)
            if age_belier >= 60:
                raise ValidationError(
                    "Le bélier a dépassé l'âge optimal (5 ans). Fertilité et vigueur peuvent être diminuées."
                )

        # --- Pas le même animal de chaque côté
        if self.boucle_belier_id and self.boucle_brebis_id and self.boucle_belier_id == self.boucle_brebis_id:
            raise ValidationError("Le bélier et la brebis ne peuvent pas être le même animal.")

        # --- Garde-fous sur sexe et activité (au cas où limit_choices_to serait contourné)
        if self.boucle_brebis:
            if self.boucle_brebis.sexe != 'femelle' or not self.boucle_brebis.boucle_active:
                raise ValidationError("La brebis doit être une femelle active.")
        if self.boucle_belier:
            if self.boucle_belier.sexe != 'male' or not self.boucle_belier.boucle_active:
                raise ValidationError("Le bélier doit être un mâle actif.")

        # --- Délai min entre 2 accouplements pour la brebis (7 mois ≈ 213 jours)
        if self.boucle_brebis and self.date_debut_lutte:
            dernier_acc_brebis = (
                Accouplement.objects
                .filter(boucle_brebis=self.boucle_brebis, date_debut_lutte__lt=self.date_debut_lutte)
                .order_by('-date_debut_lutte')
                .first()
            )
            if dernier_acc_brebis:
                delai_brebis = (self.date_debut_lutte - dernier_acc_brebis.date_debut_lutte).days
                if delai_brebis < 213:
                    raise ValidationError(
                        "La brebis n'a pas eu un repos suffisant (7 mois) depuis le dernier accouplement."
                    )

        # --- Délai min entre 2 campagnes pour le bélier (4 semaines ≈ 28 jours)
        if self.boucle_belier and self.date_debut_lutte:
            dernier_acc_belier = (
                Accouplement.objects
                .filter(boucle_belier=self.boucle_belier, date_debut_lutte__lt=self.date_debut_lutte)
                .order_by('-date_debut_lutte')
                .first()
            )
            if dernier_acc_belier:
                delai_belier = (self.date_debut_lutte - dernier_acc_belier.date_debut_lutte).days
                if delai_belier < 28:
                    raise ValidationError(
                        "Le bélier n'a pas respecté le délai minimum de 4 semaines entre deux campagnes."
                    )

    def save(self, *args, **kwargs):
        # Valide avant sauvegarde
        self.full_clean()
        # Est-ce un accouplement confirmé ?
        self.accouplement_reussi = bool(self.date_verification_gestation and self.date_gestation)
        super().save(*args, **kwargs)

    # Petit plus (facultatif)
    @property
    def duree_lutte(self):
        if self.date_debut_lutte and self.date_fin_lutte:
            return (self.date_fin_lutte - self.date_debut_lutte).days
        return None

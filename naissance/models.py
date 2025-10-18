# app: naissance (ou l'app où tu mets ces modèles)
from datetime import date
from django.db import models
from django.core.exceptions import ValidationError


class Naissance(models.Model):
    """
    Enregistre une mise-bas (naissance) d'une brebis.
    La mère est un Troupeau (sexe=femelle, actif).
    L'accouplement est optionnel (interne/externe).
    """

    boucle_mere = models.ForeignKey(
        'troupeau.Troupeau',
        on_delete=models.CASCADE,
        related_name='naissances',
        limit_choices_to={'sexe': 'femelle', 'boucle_active': True},
        verbose_name="Mère (boucle)"
    )

    accouplement = models.ForeignKey(
        'accouplement.Accouplement',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='naissances',
        verbose_name="Accouplement (si interne)"
    )

    ORIGINE_CHOIX = [
        ('Interne', 'Interne (dans la ferme)'),
        ('Externe', 'Externe (hors ferme)'),
        ('Inconnu', 'Inconnu'),
    ]
    origine_accouplement = models.CharField(
        max_length=20,
        choices=ORIGINE_CHOIX,
        default='Inconnu',
        verbose_name="Origine de l’accouplement"
    )

    nom_male_externe = models.CharField(
        max_length=50,
        blank=True, null=True,
        help_text="Nom ou boucle du mâle si accouplement externe",
        verbose_name="Mâle externe (si externe)"
    )

    date_mise_bas = models.DateField(verbose_name="Date de mise-bas")
    observations = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'naissance'
        verbose_name = "Naissance"
        verbose_name_plural = "Naissances"
        ordering = ['-date_mise_bas']
        constraints = [
            models.UniqueConstraint(
                fields=['boucle_mere', 'date_mise_bas'],
                name='uniq_naissance_mere_date'
            ),
        ]

    def __str__(self):
        return f"Naissance du {self.date_mise_bas:%d/%m/%Y} — mère {getattr(self.boucle_mere, 'boucle_ovin', '—')}"

    @property
    def pere_label(self):
        """
        Retourne une étiquette lisible du père : boucle du bélier si interne, sinon le nom externe.
        """
        if self.accouplement and getattr(self.accouplement, 'boucle_belier', None):
            return getattr(self.accouplement.boucle_belier, 'boucle_ovin', '—')
        if self.nom_male_externe:
            return self.nom_male_externe
        return "Inconnu"

    def clean(self):
        super().clean()
        errors = {}

        # Mère = femelle (double sécurité)
        if self.boucle_mere and self.boucle_mere.sexe != 'femelle':
            errors['boucle_mere'] = "La mère doit être de sexe 'Femelle'."

        # Dates simples
        if self.date_mise_bas and self.date_mise_bas > date.today():
            errors['date_mise_bas'] = "La date de mise-bas ne peut pas être dans le futur."
        if self.boucle_mere and self.boucle_mere.naissance_date and self.date_mise_bas:
            if self.date_mise_bas < self.boucle_mere.naissance_date:
                errors['date_mise_bas'] = "La date de mise-bas ne peut pas être antérieure à la naissance de la mère."

        # Cohérence origine / accouplement
        if self.origine_accouplement == 'Interne' and not self.accouplement:
            errors['accouplement'] = "Un accouplement interne doit être lié à un enregistrement d'accouplement."
        if self.origine_accouplement == 'Externe' and not self.nom_male_externe:
            errors['nom_male_externe'] = "Un accouplement externe doit mentionner un nom ou une boucle de mâle."
        if self.accouplement and self.nom_male_externe:
            errors['nom_male_externe'] = "Un accouplement ne peut pas être à la fois interne et externe."

        # Cohérence avec l’objet Accouplement (si fourni)
        if self.accouplement:
            # La femelle de l'accouplement doit être la mère
            if self.accouplement.boucle_brebis_id != self.boucle_mere_id:
                errors['accouplement'] = "La femelle dans l'accouplement ne correspond pas à la mère sélectionnée."

            # Le bélier doit être un mâle (double sécurité)
            belier = getattr(self.accouplement, 'boucle_belier', None)
            if not belier or belier.sexe != 'male':
                errors['accouplement'] = "Le bélier lié à l'accouplement doit être un animal de sexe 'Mâle'."

            # Optionnel : cohérence de période (mise-bas après début/fin de lutte)
            if self.date_mise_bas and self.accouplement.date_debut_lutte:
                if self.date_mise_bas < self.accouplement.date_debut_lutte:
                    errors['date_mise_bas'] = "La mise-bas ne peut pas précéder le début de lutte."

        if errors:
            raise ValidationError(errors)


class Agneau(models.Model):
    """
    Relie un enregistrement 'Troupeau' (le petit) à une Naissance.
    """
    naissance = models.ForeignKey(
        Naissance,
        on_delete=models.CASCADE,
        related_name="agneaux",
        verbose_name="Naissance"
    )

    boucle = models.OneToOneField(
        'troupeau.Troupeau',
        on_delete=models.CASCADE,
        related_name='enregistrement_agneau',
        limit_choices_to={'statut': 'naissance'},
        verbose_name="Boucle de l’agneau"
    )

    SEXE_CHOIX = [
        ('male', 'Mâle'),
        ('femelle', 'Femelle'),
    ]
    sexe = models.CharField(max_length=7, choices=SEXE_CHOIX)

    class Meta:
        db_table = 'agneau'
        verbose_name = "Agneau"
        verbose_name_plural = "Agneaux"

    def __str__(self):
        return f"Agneau {getattr(self.boucle, 'boucle_ovin', '—')} ({self.get_sexe_display()})"

    def clean(self):
        super().clean()
        errors = {}

        # La mère de la boucle de l’agneau doit correspondre à la mère de la Naissance
        if self.boucle and self.naissance and self.boucle.mere_boucle_id and self.naissance.boucle_mere_id:
            if self.boucle.mere_boucle_id != self.naissance.boucle_mere_id:
                errors['boucle'] = (
                    f"La mère de la boucle {self.boucle.boucle_ovin} "
                    f"ne correspond pas à la mère de la naissance."
                )

        # La boucle associée doit être marquée comme 'naissance'
        if self.boucle and self.boucle.statut != 'naissance':
            errors['boucle'] = "La boucle sélectionnée doit avoir le statut 'Naissance'."

        # Cohérence du sexe (optionnel mais utile)
        if self.boucle and self.sexe and self.boucle.sexe and self.sexe != self.boucle.sexe:
            errors['sexe'] = "Le sexe renseigné ne correspond pas au sexe de la boucle sélectionnée."

        if errors:
            raise ValidationError(errors)

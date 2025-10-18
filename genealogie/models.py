from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q, F
from django.utils.translation import gettext_lazy as _


class Genealogie(models.Model):
    agneau = models.OneToOneField(
        'troupeau.Troupeau',
        on_delete=models.CASCADE,
        related_name='genealogie',
        verbose_name=_("Agneau (boucle)")
    )
    mere = models.ForeignKey(
        'troupeau.Troupeau',
        on_delete=models.PROTECT,
        related_name='genealogies_comme_mere',
        verbose_name=_("Mère (boucle)")
    )
    pere = models.ForeignKey(
        'troupeau.Troupeau',
        on_delete=models.PROTECT,
        related_name='genealogies_comme_pere',
        verbose_name=_("Père (boucle)")
    )

    fa = models.FloatField(
        default=0.0,
        verbose_name=_("Coefficient de consanguinité (Fa)"),
        help_text=_("Stocké en base (0..1), recalculé automatiquement à l'enregistrement.")
    )

    class Meta:
        db_table = 'genealogie'
        verbose_name = _("Généalogie")
        verbose_name_plural = _("Généalogies")
        constraints = [
            models.CheckConstraint(check=~Q(agneau=F('mere')), name='genealogie_agneau_diff_mere'),
            models.CheckConstraint(check=~Q(agneau=F('pere')), name='genealogie_agneau_diff_pere'),
            models.CheckConstraint(check=~Q(mere=F('pere')), name='genealogie_mere_diff_pere'),
        ]
        indexes = [
            models.Index(fields=['agneau']),
            models.Index(fields=['mere']),
            models.Index(fields=['pere']),
        ]

    def __str__(self):
        return f"Généalogie de {getattr(self.agneau, 'boucle_ovin', self.agneau_id)}"

    # -----------------------
    # Validations métier
    # -----------------------
    def clean(self):
        super().clean()
        errors = {}

        # Identités distinctes
        if self.agneau_id and (self.agneau_id == self.mere_id or self.agneau_id == self.pere_id):
            errors['agneau'] = _("L'agneau ne peut être ni sa propre mère ni son propre père.")
        if self.mere_id and self.pere_id and self.mere_id == self.pere_id:
            errors['mere'] = _("Les deux parents doivent être différents.")

        # Sexes cohérents (si renseignés)
        if getattr(self.mere, 'sexe', None) and self.mere.sexe != 'femelle':
            errors['mere'] = _("La mère doit être de sexe féminin.")
        if getattr(self.pere, 'sexe', None) and self.pere.sexe != 'male':
            errors['pere'] = _("Le père doit être de sexe masculin.")

        # (Optionnel) Cohérence avec les FK du modèle Troupeau
        if getattr(self.agneau, 'pere_boucle_id', None) and self.agneau.pere_boucle_id != self.pere_id:
            errors['pere'] = _("Ce père ne correspond pas à celui enregistré sur l'agneau.")
        if getattr(self.agneau, 'mere_boucle_id', None) and self.agneau.mere_boucle_id != self.mere_id:
            errors['mere'] = _("Cette mère ne correspond pas à celle enregistrée sur l'agneau.")

        if errors:
            raise ValidationError(errors)

    # -----------------------
    # Outils de calcul
    # -----------------------
    def _get_parents(self, ovin):
        """
        Renvoie (pere, mere) pour un Troupeau donné.
        Priorité :
          1) la table Genealogie si dispo (plus stricte),
          2) fallback vers les FK du modèle Troupeau.
        """
        if ovin is None:
            return None, None

        try:
            g = ovin.genealogie  # peut ne pas exister
            return g.pere, g.mere
        except Genealogie.DoesNotExist:
            return getattr(ovin, 'pere_boucle', None), getattr(ovin, 'mere_boucle', None)

    def _coefficient_parente(self, ovin1, ovin2, cache):
        """
        Coefficient de parenté entre deux individus.
        Stratégie simple, symétrique, avec mémoïsation.
        """
        if ovin1 is None or ovin2 is None:
            return 0.0
        key = ('r', getattr(ovin1, 'pk', None), getattr(ovin2, 'pk', None))
        if key in cache:
            return cache[key]

        if getattr(ovin1, 'pk', None) and getattr(ovin2, 'pk', None) and ovin1.pk == ovin2.pk:
            cache[key] = 1.0
            return 1.0

        p1, m1 = self._get_parents(ovin1)
        p2, m2 = self._get_parents(ovin2)

        if p1 is None and m1 is None and p2 is None and m2 is None:
            cache[key] = 0.0
            return 0.0

        r12 = 0.5 * (self._coefficient_parente(p1, ovin2, cache) + self._coefficient_parente(m1, ovin2, cache))
        r21 = 0.5 * (self._coefficient_parente(ovin1, p2, cache) + self._coefficient_parente(ovin1, m2, cache))
        r = (r12 + r21) / 2.0

        cache[key] = r
        return r

    def _coefficient_consanguinite(self, ovin, cache):
        """
        Wright : F = 0.5(F_père + F_mère) + 0.25 * R(père, mère)
        (valeur dans 0..1). Utilise un cache pour éviter les recomputations.
        """
        if ovin is None:
            return 0.0
        key = ('f', getattr(ovin, 'pk', None))
        if key in cache:
            return cache[key]

        pere, mere = self._get_parents(ovin)
        if pere is None or mere is None:
            cache[key] = 0.0
            return 0.0

        Fp = self._coefficient_consanguinite(pere, cache)
        Fm = self._coefficient_consanguinite(mere, cache)
        rpm = self._coefficient_parente(pere, mere, cache)

        F = 0.5 * (Fp + Fm) + 0.25 * rpm
        # garde-fou numérique
        F = 0.0 if F < 0 else float(f"{F:.5f}")
        cache[key] = F
        return F

    @property
    def coefficient_consanguinite(self):
        """
        Fa renvoyé en pourcentage (ex: 12.5 pour 12.5%).
        """
        cache = {}
        fa_0_1 = self._coefficient_consanguinite(self.agneau, cache)
        return round(fa_0_1 * 100.0, 4)

    @property
    def risque_consanguinite(self):
        fa = self.coefficient_consanguinite
        if fa >= 25.0:
            return _("⚠️ Risque très élevé ({fa}%)").format(fa=fa)
        if fa >= 12.5:
            return _("⚠️ Risque élevé ({fa}%)").format(fa=fa)
        if fa >= 6.25:
            return _("⚠️ Risque modéré ({fa}%)").format(fa=fa)
        return _("✔️ Risque faible ({fa}%)").format(fa=fa)

    # -----------------------
    # Sauvegarde
    # -----------------------
    def save(self, *args, **kwargs):
        # mettre à jour fa (0..1) à chaque enregistrement
        try:
            self.fa = round(self._coefficient_consanguinite(self.agneau, cache={}), 5)
        except Exception:
            # on n’empêche pas l’enregistrement si le calcul échoue
            pass
        return super().save(*args, **kwargs)

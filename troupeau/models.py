from datetime import date
from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class Troupeau(models.Model):
    """
    Modèle représentant un animal ovin dans le troupeau
    """

    STATUT_CHOIX = [
        ('naissance', 'Naissance'),
        ('vendu', 'Vendu'),
        ('decede', 'Décédé'),
        ('sortie', 'Sortie'),
        ('pret_notre_ferme', 'Prêt notre ferme'),
        ('pret_autre_ferme', 'Prêt autre ferme'),
        ('echange_ovin', 'Échange Ovin'),
        ('achat', 'Achat'),
    ]

    PROPRIETAIRE_CHOIX = [
        ('miguel', 'Miguel'),
        ('virgile', 'Virgile'),
    ]

    SEXE_CHOIX = [
        ('male', 'Mâle'),
        ('femelle', 'Femelle'),
    ]

    RACE_CHOIX = [
        ('bali_bali', 'BALI-BALI'),
        ('balami', 'BALAMI'),
        ('oudah', 'OUDAH'),
        ('ladoun', 'LADOUN'),
        ('koundoum', 'KOUNDOUM'),
        ('macina', 'MACINA'),
    ]

    ORIGINE_CHOIX = [
        ('cotonou', 'Cotonou'),
        ('porto_novo', 'Porto-Novo'),
        ('abomey_calavi', 'Abomey-Calavi'),
        ('ouidah', 'Ouidah'),
        ('seme_kpodji', 'Sèmè-Kpodji'),
        ('akpakpa', 'Akpakpa'),
        ('godomey', 'Godomey'),
        ('tori_bossito', 'Tori-Bossito'),
        ('pahou', 'Pahou'),
        ('avrankou', 'Avrankou'),
        ('ifangni', 'Ifangni'),
        ('ketou', 'Kétou'),
        ('come', 'Comè'),
        ('lokossa', 'Lokossa'),
        ('dassa_zoume', 'Dassa-Zoumé'),
    ]

    # Champs principaux
    boucle_ovin = models.CharField(
        max_length=20,
        verbose_name=_("Numéro de boucle"),
        help_text=_("Identifiant de l'animal (réutilisable quand inactif)")
    )

    sexe = models.CharField(
        max_length=10,
        choices=SEXE_CHOIX,
        verbose_name=_("Sexe")
    )

    race = models.CharField(
        max_length=50,
        choices=RACE_CHOIX,
        verbose_name=_("Race")
    )

    naissance_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Date de naissance")
    )

    boucle_active = models.BooleanField(
        default=True,
        verbose_name=_("Boucle active"),
        help_text=_("Indique si l'animal est encore dans le troupeau")
    )

    # Mesures physiques
    poids_initial = models.FloatField(
        blank=True,
        null=True,
        verbose_name=_("Poids initial (kg)"),
        help_text=_("Poids à l'entrée ou à la naissance")
    )

    taille_initiale = models.FloatField(
        blank=True,
        null=True,
        verbose_name=_("Taille initiale (cm)"),
        help_text=_("Hauteur au garrot")
    )

    # Relations parentales (related_name alignés avec admin & vues)
    pere_boucle = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agneaux_pere',
        limit_choices_to={'sexe': 'male', 'boucle_active': True},
        verbose_name=_("Père")
    )

    mere_boucle = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agneaux_mere',
        limit_choices_to={'sexe': 'femelle', 'boucle_active': True},
        verbose_name=_("Mère")
    )

    # Dates importantes
    achat_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Date d'achat")
    )

    entree_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Date d'entrée"),
        help_text=_("Date d'arrivée dans la ferme")
    )

    date_sortie = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Date de sortie")
    )

    # Informations administratives
    statut = models.CharField(
        max_length=30,
        choices=STATUT_CHOIX,
        verbose_name=_("Statut")
    )

    origine_ovin = models.CharField(
        max_length=50,
        choices=ORIGINE_CHOIX,
        verbose_name=_("Origine")
    )

    proprietaire_ovin = models.CharField(
        max_length=50,
        choices=PROPRIETAIRE_CHOIX,
        verbose_name=_("Propriétaire")
    )

    observations = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Observations"),
        help_text=_("Notes diverses sur l'animal")
    )

    # Coefficient de consanguinité
    coefficient_consanguinite = models.FloatField(
        default=0.0,
        verbose_name=_("Coefficient de consanguinité"),
        help_text=_("Calculé automatiquement selon Wright")
    )

    # Champs de métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'troupeau'
        verbose_name = _("Animal du troupeau")
        verbose_name_plural = _("Animaux du troupeau")
        ordering = ['-naissance_date']
        indexes = [
            models.Index(fields=['boucle_ovin']),
            models.Index(fields=['sexe']),
            models.Index(fields=['race']),
            models.Index(fields=['statut']),
            models.Index(fields=['boucle_active']),
        ]
        # Unicité conditionnelle : une seule boucle active à la fois
        constraints = [
            models.UniqueConstraint(
                fields=['boucle_ovin'],
                condition=Q(boucle_active=True),
                name='uniq_boucle_ovin_active',
            ),
        ]

    def __str__(self):
        # ok d'utiliser get_*_display() (méthode auto des champs à choices)
        return f"{self.boucle_ovin} ({self.get_sexe_display()})"

    # ---- Propriétés d'âge ----
    @property
    def age_ovin(self):
        """Âge en années (int)"""
        if not self.naissance_date:
            return None
        today = date.today()
        age = today.year - self.naissance_date.year
        if (today.month, today.day) < (self.naissance_date.month, self.naissance_date.day):
            age -= 1
        return max(0, age)

    @property
    def age_en_mois(self):
        """Âge en mois (int)"""
        if not self.naissance_date:
            return None
        today = date.today()
        mois = (today.year - self.naissance_date.year) * 12 + (today.month - self.naissance_date.month)
        if today.day < self.naissance_date.day:
            mois -= 1
        return max(0, mois)

    @property
    def is_reproducteur_age(self):
        """True si l'animal est dans la tranche d'âge reproducteur"""
        age_mois = self.age_en_mois
        if age_mois is None:
            return False
        return (8 <= age_mois <= 84) if self.sexe == 'male' else (10 <= age_mois <= 96)

    # ---- Validation ----
    def clean(self):
        super().clean()
        errors = {}
        today = date.today()

        # Futur interdit
        if self.naissance_date and self.naissance_date > today:
            errors['naissance_date'] = _("La date de naissance ne peut pas être dans le futur.")
        if self.achat_date and self.achat_date > today:
            errors['achat_date'] = _("La date d'achat ne peut pas être dans le futur.")
        if self.entree_date and self.entree_date > today:
            errors['entree_date'] = _("La date d'entrée ne peut pas être dans le futur.")
        if self.date_sortie and self.date_sortie > today:
            errors['date_sortie'] = _("La date de sortie ne peut pas être dans le futur.")

        # Ordre logique des dates
        if self.naissance_date:
            if self.achat_date and self.naissance_date > self.achat_date:
                errors['achat_date'] = _("La date d'achat doit être postérieure à la date de naissance.")
            if self.entree_date and self.naissance_date > self.entree_date:
                errors['entree_date'] = _("La date d'entrée doit être postérieure à la date de naissance.")
            if self.date_sortie and self.naissance_date > self.date_sortie:
                errors['date_sortie'] = _("La date de sortie doit être postérieure à la date de naissance.")

        if self.achat_date and self.entree_date and self.entree_date < self.achat_date:
            errors['entree_date'] = _("La date d'entrée ne peut pas être antérieure à la date d'achat.")
        if self.entree_date and self.date_sortie and self.date_sortie < self.entree_date:
            errors['date_sortie'] = _("La date de sortie ne peut pas être antérieure à la date d'entrée.")

        # Mesures positives
        if self.poids_initial is not None and self.poids_initial <= 0:
            errors['poids_initial'] = _("Le poids doit être positif.")
        if self.taille_initiale is not None and self.taille_initiale <= 0:
            errors['taille_initiale'] = _("La taille doit être positive.")

        # Parents cohérents
        if self.pere_boucle == self:
            errors['pere_boucle'] = _("Un animal ne peut pas être son propre père.")
        if self.mere_boucle == self:
            errors['mere_boucle'] = _("Un animal ne peut pas être sa propre mère.")
        if self.pere_boucle and self.mere_boucle and self.pere_boucle == self.mere_boucle:
            errors['mere_boucle'] = _("Le père et la mère ne peuvent pas être le même animal.")

        if self.pere_boucle:
            if self.pere_boucle.sexe != 'male':
                errors['pere_boucle'] = _("Le père doit être un animal de sexe masculin.")
            if not self.pere_boucle.boucle_active:
                errors['pere_boucle'] = _("Le père doit être un animal actif dans le troupeau.")
        if self.mere_boucle:
            if self.mere_boucle.sexe != 'femelle':
                errors['mere_boucle'] = _("La mère doit être un animal de sexe féminin.")
            if not self.mere_boucle.boucle_active:
                errors['mere_boucle'] = _("La mère doit être un animal actif dans le troupeau.")

        # Unicité de la boucle active
        if self.boucle_active:
            existing = Troupeau.objects.filter(
                boucle_ovin=self.boucle_ovin,
                boucle_active=True
            ).exclude(pk=self.pk)
            if existing.exists():
                errors['boucle_ovin'] = _("Cette boucle est déjà active pour un autre animal.")

        if errors:
            raise ValidationError(errors)

    # ---- Généalogie ----
    def _get_ancestors_paths(self, current, max_depth, path=None, ancestors=None, visited=None):
        """
        Retourne un dict {ancêtre: [(distance_pere, distance_mere), ...]} jusqu'à max_depth.
        Protégé contre les boucles infinies.
        """
        if ancestors is None:
            ancestors = {}
        if path is None:
            path = (0, 0)
        if visited is None:
            visited = set()

        if max_depth == 0 or not current or current.pk in visited:
            return ancestors

        visited.add(current.pk)

        if current != self:
            ancestors.setdefault(current, []).append(path)

        try:
            if current.pere_boucle:
                self._get_ancestors_paths(
                    current.pere_boucle, max_depth - 1,
                    (path[0] + 1, path[1]), ancestors, visited.copy()
                )
            if current.mere_boucle:
                # ✅ correction: utiliser la bonne signature/ordre des paramètres
                self._get_ancestors_paths(
                    current.mere_boucle, max_depth - 1,
                    (path[0], path[1] + 1), ancestors, visited.copy()
                )
        except RecursionError:
            pass

        return ancestors

    def coefficient_consanguinite_wright(self, max_generations=3, cache=None):
        """
        Coefficient de consanguinité de Wright (récursif, avec cache et garde-fous).
        """
        if cache is None:
            cache = {}

        if self.pk and self.pk in cache:
            return cache[self.pk]

        if not self.pere_boucle or not self.mere_boucle:
            if self.pk:
                cache[self.pk] = 0.0
            return 0.0

        if max_generations <= 0:
            if self.pk:
                cache[self.pk] = 0.0
            return 0.0

        try:
            pere_anc = self._get_ancestors_paths(self.pere_boucle, max_generations)
            mere_anc = self._get_ancestors_paths(self.mere_boucle, max_generations)
            communs = set(pere_anc.keys()).intersection(mere_anc.keys())

            if not communs:
                if self.pk:
                    cache[self.pk] = 0.0
                return 0.0

            F = 0.0
            for anc in communs:
                dist_p = min(d[0] for d in pere_anc[anc])
                dist_m = min(d[1] for d in mere_anc[anc])
                Fa = anc.coefficient_consanguinite_wright(
                    max_generations=max_generations - 1, cache=cache
                )
                F += (1 / 2) ** (dist_p + dist_m + 1) * (1 + Fa)

            F = round(F, 5)
            if self.pk:
                cache[self.pk] = F
            return F

        except (RecursionError, AttributeError):
            if self.pk:
                cache[self.pk] = 0.0
            return 0.0

    def get_descendants(self):
        """Descendants directs"""
        return self.agneaux_pere.all() if self.sexe == 'male' else self.agneaux_mere.all()

    def get_all_descendants(self, max_depth=3):
        """Descendants jusqu'à max_depth générations"""
        descendants = set()

        def _collect(animal, depth):
            if depth <= 0:
                return
            for child in animal.get_descendants():
                if child not in descendants:
                    descendants.add(child)
                    _collect(child, depth - 1)

        _collect(self, max_depth)
        return list(descendants)

    # ---- Sauvegarde ----
    def save(self, *args, **kwargs):
        """Sauvegarde avec mise à jour auto de boucle_active et du coefficient."""
        # Adapter boucle_active selon le statut (ne **force** pas True)
        if self.statut in ['vendu', 'decede', 'sortie']:
            self.boucle_active = False

        # Validation
        self.full_clean()

        # Sauvegarde initiale
        super().save(*args, **kwargs)

        # Mise à jour coefficient sans reboucler
        nouveau = self.coefficient_consanguinite_wright()
        if abs((self.coefficient_consanguinite or 0.0) - nouveau) > 0.00001:
            self.coefficient_consanguinite = nouveau
            Troupeau.objects.filter(pk=self.pk).update(coefficient_consanguinite=nouveau)

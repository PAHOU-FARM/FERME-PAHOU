from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from decimal import Decimal
from datetime import date

# Import des autres modules (références paresseuses possibles ailleurs si besoin)
from troupeau.models import Troupeau
from maladie.models import Maladie
from vaccination.models import Vaccination


class MotifVisite(models.TextChoices):
    DIAGNOSTIC = (
        'Diagnostic et traitement des maladies',
        'Diagnostic et traitement des maladies',
    )
    VACCINATIONS = (
        'Vaccinations préventives',
        'Vaccinations préventives',
    )
    SUIVI_CHRONIQUE = (
        'Suivi des cas chroniques ou graves',
        'Suivi des cas chroniques ou graves',
    )
    ASSISTANCE_REPRO = (
        "Assistance lors des avortements ou troubles de la reproduction",
        "Assistance lors des avortements ou troubles de la reproduction",
    )
    INTERVENTIONS = (
        'Interventions chirurgicales ou urgentes',
        'Interventions chirurgicales ou urgentes',
    )
    CONTROLES = (
        'Contrôles sanitaires réglementaires',
        'Contrôles sanitaires réglementaires',
    )
    EVALUATION_TROUPEAU = (
        "Évaluation de l'état général du troupeau",
        "Évaluation de l'état général du troupeau",
    )
    PRESCRIPTIONS = (
        'Prescriptions de médicaments',
        'Prescriptions de médicaments',
    )


class TraitementEffectue(models.TextChoices):
    IDENTIFICATION = (
        'Identification des pathologies et prescription de médicaments adaptés',
        'Identification des pathologies et prescription de médicaments adaptés',
    )
    PROTECTION = (
        'Protection contre la brucellose, fièvre catarrhale',
        'Protection contre la brucellose, fièvre catarrhale',
    )
    SURVEILLANCE = (
        'Surveillance des animaux atteints de maladies persistantes',
        'Surveillance des animaux atteints de maladies persistantes',
    )
    REPRODUCTION = (
        'Traitement des avortements, infertilités, rétentions placentaires',
        'Traitement des avortements, infertilités, rétentions placentaires',
    )
    PLAIES = (
        'Intervention sur plaies, abcès ou boiteries sévères',
        'Intervention sur plaies, abcès ou boiteries sévères',
    )
    VERIFICATION = (
        "Vérification lors des ventes, abattages ou transports d'ovins",
        "Vérification lors des ventes, abattages ou transports d'ovins",
    )
    ANALYSE_GENERALE = (
        "Analyse générale pour améliorer nutrition, reproduction ou bien-être",
        "Analyse générale pour améliorer nutrition, reproduction ou bien-être",
    )
    PRODUITS_REGLEMENTES = (
        "Certains produits sont strictement délivrés par un vétérinaire",
        "Certains produits sont strictement délivrés par un vétérinaire",
    )


class Veterinaire(models.Model):
    date_visite = models.DateField()
    nom_veterinaire = models.CharField(max_length=100)

    # Liens vers les autres modules
    troupeau = models.ForeignKey(Troupeau, on_delete=models.CASCADE)
    maladie = models.ForeignKey(Maladie, on_delete=models.SET_NULL, null=True, blank=True)
    vaccination = models.ForeignKey(Vaccination, on_delete=models.SET_NULL, null=True, blank=True)

    motif_de_la_visite = models.CharField(
        max_length=100,
        choices=MotifVisite.choices
    )
    traitement_effectue = models.CharField(
        max_length=150,
        choices=TraitementEffectue.choices
    )
    recommandations = models.TextField()
    cout_visite = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    observations = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('date_visite', 'nom_veterinaire', 'troupeau')
        verbose_name = "Visite vétérinaire"
        verbose_name_plural = "Visites vétérinaires"
        ordering = ['-date_visite']
        indexes = [
            models.Index(fields=['date_visite']),
            models.Index(fields=['nom_veterinaire']),
            models.Index(fields=['troupeau']),
        ]

    def __str__(self):
        try:
            boucle = getattr(self.troupeau, 'boucle_ovin', None) or str(self.troupeau)
        except Exception:
            boucle = '—'
        return f"{self.nom_veterinaire} — {self.date_visite} — {boucle}"

    # ---- Helpers internes pour rester compatible avec la casse des autres apps
    @staticmethod
    def _boucle_of_maladie(maladie: Maladie):
        """
        Retourne l'instance Troupeau liée à la Maladie, en supportant
        aussi bien 'Boucle_Ovin' (ancien schéma) que 'boucle_ovin' (schéma normalisé).
        """
        if maladie is None:
            return None
        return getattr(maladie, 'Boucle_Ovin', None) or getattr(maladie, 'boucle_ovin', None)

    def clean(self):
        super().clean()

        # Date non future
        if self.date_visite and self.date_visite > date.today():
            raise ValidationError({"date_visite": "La date de visite ne peut pas être dans le futur."})

        # Coût non négatif (le validator couvre déjà 0+, on garde un message clair ici si contourné)
        if self.cout_visite is not None and self.cout_visite < 0:
            raise ValidationError({"cout_visite": "Le coût de la visite ne peut pas être négatif."})

        # Cohérence des FK : si une maladie est indiquée, elle doit concerner le même ovin
        if self.maladie:
            malade_ovin = self._boucle_of_maladie(self.maladie)
            if malade_ovin and self.troupeau and malade_ovin != self.troupeau:
                raise ValidationError(
                    "La maladie sélectionnée n'appartient pas au même ovin que la visite."
                )

        # Cohérence des FK : si une vaccination est indiquée, elle doit concerner le même ovin
        if self.vaccination:
            # Vaccination normalisée : champ 'boucle_ovin'
            vacc_ovin = getattr(self.vaccination, 'boucle_ovin', None)
            if vacc_ovin and self.troupeau and vacc_ovin != self.troupeau:
                raise ValidationError(
                    "La vaccination sélectionnée n'appartient pas au même ovin que la visite."
                )

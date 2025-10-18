from datetime import timedelta, date

from django.core.exceptions import ValidationError
from django.db import models

from troupeau.models import Troupeau

# Durée moyenne de gestation (à ajuster si besoin)
GESTATION_DUREE_JOURS = 150


class Gestation(models.Model):
    METHODE_CHOIX = [
        ("Palpation", "Palpation"),
        ("Echographie", "Échographie"),
        ("Observation comportementale", "Observation comportementale"),
    ]

    # Valeur en base sans accent pour éviter les soucis de normalisation
    ETAT_CHOIX = [
        ("Confirmée", "Confirmée"),
        ("Non Confirmée", "Non Confirmée"),
        ("A surveiller", "À surveiller"),
    ]

    boucle_brebis = models.ForeignKey(
        Troupeau,
        on_delete=models.CASCADE,
        limit_choices_to={"sexe": "femelle", "boucle_active": True},
        verbose_name="Brebis",
        db_index=True,
    )

    date_gestation = models.DateField(
        default=date.today,
        verbose_name="Date de gestation",
        db_index=True,
    )

    methode_confirmation = models.CharField(
        max_length=30,
        choices=METHODE_CHOIX,
        verbose_name="Méthode de confirmation",
        db_index=True,
    )

    etat_gestation = models.CharField(
        max_length=30,
        choices=ETAT_CHOIX,
        verbose_name="État de gestation",
        db_index=True,
    )

    observations = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observations",
    )

    class Meta:
        verbose_name = "Gestation"
        verbose_name_plural = "Gestations"
        ordering = ["-date_gestation", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["boucle_brebis", "date_gestation"],
                name="uniq_gestation_brebis_jour",
            ),
        ]
        indexes = [
            models.Index(fields=["boucle_brebis"]),
            models.Index(fields=["date_gestation"]),
            models.Index(fields=["etat_gestation"]),
        ]

    def __str__(self):
        boucle = getattr(self.boucle_brebis, "boucle_ovin", str(self.boucle_brebis_id))
        return f"Gestation de {boucle} le {self.date_gestation}"

    def clean(self):
        super().clean()

        # Tolère deux noms possibles du champ date de naissance dans Troupeau
        birth_date = (
            getattr(self.boucle_brebis, "naissance_date", None)
            or getattr(self.boucle_brebis, "date_naissance", None)
        )
        if birth_date is None:
            raise ValidationError("La date de naissance de la brebis est inconnue.")

        # Âge minimal 8 mois à la date de gestation
        age_brebis_mois = (self.date_gestation - birth_date).days / 30.44
        if age_brebis_mois < 8:
            raise ValidationError(
                "La brebis n'a pas l'âge minimum requis (8 mois) pour une gestation."
            )

        # Délai minimal ~7 mois (213 jours) entre deux gestations
        dernier_suivi = (
            Gestation.objects.filter(
                boucle_brebis=self.boucle_brebis, date_gestation__lt=self.date_gestation
            )
            .order_by("-date_gestation")
            .first()
        )
        if dernier_suivi:
            delai_jours = (self.date_gestation - dernier_suivi.date_gestation).days
            if delai_jours < 213:
                raise ValidationError(
                    "Le délai recommandé de 7 mois entre gestations n'est pas respecté."
                )

        # Saisie unique par jour si Non confirmée / À surveiller (garde-fou amont)
        if self.etat_gestation in ["Non Confirmée", "A surveiller"]:
            deja_saisi = (
                Gestation.objects.filter(
                    boucle_brebis=self.boucle_brebis,
                    date_gestation=self.date_gestation,
                )
                .exclude(pk=self.pk)
                .exists()
            )
            if deja_saisi:
                raise ValidationError(
                    "Une saisie existe déjà aujourd'hui pour cette brebis."
                )

        # Interdire une saisie non confirmée si une confirmée existe déjà
        if self.etat_gestation != "Confirmée":
            gestation_confirmee_existe = (
                Gestation.objects.filter(
                    boucle_brebis=self.boucle_brebis, etat_gestation="Confirmée"
                )
                .exclude(pk=self.pk)
                .exists()
            )
            if gestation_confirmee_existe:
                raise ValidationError(
                    "Cette brebis a déjà une gestation confirmée active."
                )

    def save(self, *args, **kwargs):
        # Validation complète avant sauvegarde
        self.full_clean()
        return super().save(*args, **kwargs)

    @property
    def date_estimee_mise_bas(self):
        """Date estimée de mise-bas (≈ 150 jours après la gestation)."""
        return (
            self.date_gestation + timedelta(days=GESTATION_DUREE_JOURS)
            if self.date_gestation
            else None
        )

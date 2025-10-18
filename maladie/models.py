from django.db import models
from django.core.exceptions import ValidationError
from datetime import date


class Maladie(models.Model):
    SYMPTOMES_CHOICES = [
        ('Fièvre', 'Fièvre'),
        ('Amaigrissement', 'Amaigrissement'),
        ('Anorexie', 'Anorexie'),
        ('Diarrhée', 'Diarrhée'),
        ('Jetage nasal', 'Jetage nasal'),
        ('Jetage oculaire', 'Jetage oculaire'),
        ('Toux', 'Toux'),
        ('Dyspnée', 'Dyspnée'),
        ('Boiterie', 'Boiterie'),
        ('Marche en cercle', 'Marche en cercle'),
        ('Paralysie', 'Paralysie'),
        ('Cécité', 'Cécité'),
        ('Tremblements', 'Tremblements'),
        ('Convulsions', 'Convulsions'),
        ('Ulcérations buccales', 'Ulcérations buccales'),
        ('Croûtes cutanées', 'Croûtes cutanées'),
        ('Œdème de la tête', 'Œdème de la tête'),
        ('Œdème sous-glossien', 'Œdème sous-glossien'),
        ('Perte de laine', 'Perte de laine'),
        ('Hyperesthésie', 'Hyperesthésie'),
        ('Comportement agité', 'Comportement agité'),
        ('Avortement', 'Avortement'),
        ('Rétention placentaire', 'Rétention placentaire'),
        ('Baisse de fertilité', 'Baisse de fertilité'),
        ('Dermatite', 'Dermatite'),
        ('Conjonctivite', 'Conjonctivite'),
        ('Cachexie', 'Cachexie'),
    ]

    NOM_CHOICES = [
        ('Peste des petits ruminants', 'Peste des petits ruminants'),
        ('Clavelée', 'Clavelée'),
        ('Brucellose', 'Brucellose'),
        ('Pasteurellose', 'Pasteurellose'),
        ('Strongyloses digestives', 'Strongyloses digestives'),
        ('Fasciolose', 'Fasciolose'),
        ('Oestrose', 'Oestrose'),
        ('Coenurose', 'Coenurose'),
        ('Toxémie de gestation', 'Toxémie de gestation'),
        ('Hypocalcémie', 'Hypocalcémie'),
        ('Carence en cuivre', 'Carence en cuivre'),
        ('Fièvre catarrhale ovine', 'Fièvre catarrhale ovine'),
        ('Ecthyma contagieux', 'Ecthyma contagieux'),
    ]

    TRAITEMENT_CHOICES = [
        ('Antibiotique', 'Antibiotique'),
        ('Antiparasitaire', 'Antiparasitaire'),
        ('Antipyrétique', 'Antipyrétique'),
        ('Vermifuge', 'Vermifuge'),
        ('Sérum injectable', 'Sérum injectable'),
        ('Vaccin', 'Vaccin'),
        ('Supplément minéral', 'Supplément minéral'),
        ('Hydratation IV', 'Hydratation IV'),
        ('Antifongique', 'Antifongique'),
        ('Chirurgie locale', 'Chirurgie locale'),
        ('Nettoyage des plaies', 'Nettoyage des plaies'),
        ('Traitement symptomatique', 'Traitement symptomatique'),
    ]

    GRAVITE_CHOICES = [
        ('Léger', 'Léger'),
        ('Modéré', 'Modéré'),
        ('Grave', 'Grave'),
        ('Critique', 'Critique'),
    ]

    STATUT_CHOICES = [
        ('Actif', 'Actif'),
        ('Résolu', 'Résolu'),
        ('Chronique', 'Chronique'),
    ]

    # ✅ Référence paresseuse pour éviter les imports circulaires
    Boucle_Ovin = models.ForeignKey(
        'troupeau.Troupeau',
        on_delete=models.CASCADE,
        related_name='maladies',
        help_text="Sélectionnez l'ovin concerné"
    )

    Date_observation = models.DateField(help_text="Date d'apparition des symptômes")
    Date_guerison = models.DateField(blank=True, null=True, help_text="Date de disparition des symptômes")

    Symptomes_Observes = models.CharField(max_length=50, choices=SYMPTOMES_CHOICES)
    Nom_Maladie = models.CharField(max_length=50, choices=NOM_CHOICES)

    Traitement_Administre = models.CharField(
        max_length=50, choices=TRAITEMENT_CHOICES, blank=True, null=True
    )
    Duree_Traitement = models.PositiveIntegerField(blank=True, null=True, help_text="Durée en jours")

    Cout_Traitement_FCFA = models.DecimalField(max_digits=10, decimal_places=2)

    Gravite = models.CharField(max_length=20, choices=GRAVITE_CHOICES, blank=True, null=True)
    Statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='Actif')

    Veterinaire = models.CharField(max_length=100)
    Observations = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = (
            'Boucle_Ovin', 'Nom_Maladie', 'Date_observation', 'Symptomes_Observes', 'Traitement_Administre'
        )
        ordering = ['-Date_observation']
        verbose_name = 'Maladie'
        verbose_name_plural = 'Maladies'
        indexes = [
            models.Index(fields=['Boucle_Ovin']),
            models.Index(fields=['Date_observation']),
            models.Index(fields=['Nom_Maladie']),
        ]

    def clean(self):
        today = date.today()

        if self.Date_observation and self.Date_observation > today:
            raise ValidationError({'Date_observation': "La date d'observation ne peut pas être dans le futur."})

        if self.Date_guerison:
            if self.Date_observation and self.Date_guerison < self.Date_observation:
                raise ValidationError({'Date_guerison': "La date de guérison doit être postérieure à la date d'observation."})
            # Si guéri → statut 'Résolu'
            if self.Statut != 'Résolu':
                raise ValidationError({'Statut': "Si une date de guérison est renseignée, le statut doit être 'Résolu'."})

        # Si statut 'Résolu' → exiger une date de guérison
        if self.Statut == 'Résolu' and not self.Date_guerison:
            raise ValidationError({'Date_guerison': "Renseignez la date de guérison pour un cas 'Résolu'."})

        if self.Cout_Traitement_FCFA is not None and self.Cout_Traitement_FCFA < 0:
            raise ValidationError({'Cout_Traitement_FCFA': "Le coût du traitement ne peut pas être négatif."})

        if self.Duree_Traitement is not None and self.Duree_Traitement <= 0:
            raise ValidationError({'Duree_Traitement': "La durée de traitement doit être strictement positive."})

        # Cohérence simple avec la naissance si dispo (sans casser en cas de champ absent)
        naissance = getattr(self.Boucle_Ovin, 'naissance_date', None)
        if self.Date_observation and naissance and self.Date_observation < naissance:
            raise ValidationError({'Date_observation': "La date d’observation ne peut pas être antérieure à la naissance de l’animal."})

    def __str__(self):
        boucle = getattr(self.Boucle_Ovin, 'boucle_ovin', self.Boucle_Ovin_id)
        return f"{boucle} - {self.Nom_Maladie} ({self.Date_observation})"

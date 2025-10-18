from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Croissance
from troupeau.models import Troupeau


class CroissanceForm(forms.ModelForm):
    class Meta:
        model = Croissance
        # On n’édite pas Age_en_Mois (calculé) ni est_historique (géré par le système)
        fields = [
            'Boucle_Ovin',
            'Date_mesure',
            'Poids_Kg',
            'Taille_CM',
            'Etat_Sante',
            'Croissance_Evaluation',
            'Observations',
        ]
        widgets = {
            'Boucle_Ovin': forms.Select(attrs={'class': 'form-select'}),
            'Date_mesure': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'Poids_Kg': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'form-control'}),
            'Taille_CM': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'form-control'}),
            'Etat_Sante': forms.Select(attrs={'class': 'form-select'}),
            'Croissance_Evaluation': forms.Select(attrs={'class': 'form-select'}),
            'Observations': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
        labels = {
            'Boucle_Ovin': 'Boucle Ovin',
            'Date_mesure': 'Date de mesure',
            'Poids_Kg': 'Poids (kg)',
            'Taille_CM': 'Taille (cm)',
            'Etat_Sante': 'État de santé',
            'Croissance_Evaluation': 'Évaluation de croissance',
            'Observations': 'Observations',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Proposer en priorité les animaux actifs, triés par numéro de boucle
        qs = Troupeau.objects.all().order_by('boucle_ovin')
        try:
            qs = qs.filter(boucle_active=True)
        except Exception:
            pass

        self.fields['Boucle_Ovin'].queryset = qs
        self.fields['Boucle_Ovin'].empty_label = "— Sélectionner un animal —"
        self.fields['Boucle_Ovin'].label_from_instance = (
            lambda obj: f"{obj.boucle_ovin} — {obj.get_sexe_display()} / {obj.get_race_display()}"
            if hasattr(obj, 'get_sexe_display') and hasattr(obj, 'get_race_display')
            else f"{obj.boucle_ovin}"
        )

    # Validations ciblées (douces) — le modèle refera un contrôle global
    def clean_Date_mesure(self):
        d = self.cleaned_data.get('Date_mesure')
        if d and d > timezone.localdate():
            raise ValidationError("La date ne peut pas être dans le futur.")
        bov = self.cleaned_data.get('Boucle_Ovin')
        if d and bov and getattr(bov, 'naissance_date', None) and d < bov.naissance_date:
            raise ValidationError("La date de mesure ne peut pas être antérieure à la naissance.")
        return d

    def clean_Poids_Kg(self):
        x = self.cleaned_data.get('Poids_Kg')
        if x is None:
            return x
        if x <= 0:
            raise ValidationError("Le poids doit être strictement positif.")
        return x

    def clean_Taille_CM(self):
        x = self.cleaned_data.get('Taille_CM')
        if x is None:
            return x
        if x <= 0:
            raise ValidationError("La taille doit être strictement positive.")
        return x

    def clean(self):
        """
        Doublon amont : (Boucle_Ovin, Date_mesure, est_historique=False).
        Laisse la DB/Model gérer la contrainte finale.
        """
        cleaned = super().clean()
        bov = cleaned.get('Boucle_Ovin')
        d = cleaned.get('Date_mesure')

        if not bov or not d:
            return cleaned

        qs = Croissance.objects.filter(
            Boucle_Ovin=bov,
            Date_mesure=d,
            est_historique=False
        )
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            self.add_error('Date_mesure', "Une mesure (non historique) existe déjà pour cet ovin à cette date.")
        return cleaned

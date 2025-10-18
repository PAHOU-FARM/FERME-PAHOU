from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Gestation
from troupeau.models import Troupeau


class GestationForm(forms.ModelForm):
    class Meta:
        model = Gestation
        fields = [
            "boucle_brebis",
            "date_gestation",
            "methode_confirmation",
            "etat_gestation",
            "observations",
        ]
        widgets = {
            "boucle_brebis": forms.Select(attrs={"class": "form-select"}),
            "date_gestation": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "methode_confirmation": forms.Select(attrs={"class": "form-select"}),
            "etat_gestation": forms.Select(attrs={"class": "form-select"}),
            "observations": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }
        labels = {
            "boucle_brebis": "Brebis",
            "date_gestation": "Date de gestation",
            "methode_confirmation": "Méthode de confirmation",
            "etat_gestation": "État de gestation",
            "observations": "Observations",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Limiter aux femelles actives, triées par numéro de boucle
        qs = Troupeau.objects.all().order_by("boucle_ovin")
        if hasattr(Troupeau, "sexe") and hasattr(Troupeau, "boucle_active"):
            qs = qs.filter(sexe="femelle", boucle_active=True)
        self.fields["boucle_brebis"].queryset = qs
        self.fields["boucle_brebis"].empty_label = "— Sélectionner une brebis —"

        # Label lisible dans le select
        def _label(o):
            sex = o.get_sexe_display() if hasattr(o, "get_sexe_display") else o.sexe
            race = o.get_race_display() if hasattr(o, "get_race_display") else o.race
            return f"{o.boucle_ovin} — {sex}/{race}"
        self.fields["boucle_brebis"].label_from_instance = _label

    # Validations ciblées côté form (complémentaires du modèle & des signaux)
    def clean_date_gestation(self):
        d = self.cleaned_data.get("date_gestation")
        if d and d > timezone.localdate():
            raise ValidationError("La date de gestation ne peut pas être dans le futur.")
        # Vérifier cohérence avec la naissance si connue
        brebis = self.cleaned_data.get("boucle_brebis")
        if d and brebis and getattr(brebis, "naissance_date", None) and d < brebis.naissance_date:
            raise ValidationError("La date de gestation ne peut pas être antérieure à la naissance de la brebis.")
        return d

    def clean(self):
        cleaned = super().clean()
        # Empêcher un doublon (même brebis + même date) en amont de la contrainte unique
        b = cleaned.get("boucle_brebis")
        d = cleaned.get("date_gestation")
        if b and d:
            qs = Gestation.objects.filter(boucle_brebis=b, date_gestation=d)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error("date_gestation", "Un enregistrement existe déjà pour cette brebis à cette date.")
        return cleaned

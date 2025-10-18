# vaccination/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
import re

from .models import Vaccination
from troupeau.models import Troupeau


class VaccinationForm(forms.ModelForm):
    class Meta:
        model = Vaccination
        fields = [
            "boucle_ovin",
            "date_vaccination",
            "type_vaccin",
            "nom_vaccin",
            "dose_vaccin",
            "voie_administration",
            "nom_veterinaire",
            "observations",
        ]
        widgets = {
            "boucle_ovin": forms.Select(attrs={"class": "form-select"}),
            "date_vaccination": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "type_vaccin": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: PPR, Clavelée…"}),
            "nom_vaccin": forms.TextInput(attrs={"class": "form-control"}),
            "dose_vaccin": forms.NumberInput(attrs={"step": "0.01", "min": "0", "class": "form-control"}),
            "voie_administration": forms.Select(attrs={"class": "form-select"}),
            "nom_veterinaire": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nom et prénom(s)"}),
            "observations": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }
        labels = {
            "boucle_ovin": "Boucle Ovin",
            "date_vaccination": "Date de vaccination",
            "type_vaccin": "Type de vaccin",
            "nom_vaccin": "Nom du vaccin",
            "dose_vaccin": "Dose (mL)",
            "voie_administration": "Voie d’administration",
            "nom_veterinaire": "Nom du vétérinaire",
            "observations": "Observations",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Proposer par défaut les animaux actifs (si le champ existe), triés par boucle
        qs = Troupeau.objects.all().order_by("boucle_ovin")
        if hasattr(Troupeau, "boucle_active"):
            qs = qs.filter(boucle_active=True)
        self.fields["boucle_ovin"].queryset = qs
        self.fields["boucle_ovin"].empty_label = "— Sélectionner un animal —"

        # Libellé lisible dans la liste déroulante
        def _label(obj: Troupeau) -> str:
            sexe_display = getattr(obj, "get_sexe_display", None)
            race_display = getattr(obj, "get_race_display", None)
            sexe = sexe_display() if callable(sexe_display) else getattr(obj, "sexe", "")
            race = race_display() if callable(race_display) else getattr(obj, "race", "")
            return f"{obj.boucle_ovin} — {sexe} / {race}"

        self.fields["boucle_ovin"].label_from_instance = _label

    # ------- Validations -------

    def clean_date_vaccination(self):
        d = self.cleaned_data.get("date_vaccination")
        if d and d > timezone.localdate():
            raise ValidationError("La date ne peut pas être dans le futur.")
        return d

    def clean_dose_vaccin(self):
        v = self.cleaned_data.get("dose_vaccin")
        if v is None:
            return v
        if v <= 0:
            raise ValidationError("La dose doit être un nombre positif.")
        return v

    def clean_nom_veterinaire(self):
        n = (self.cleaned_data.get("nom_veterinaire") or "").strip()
        # Lettres, accents, espaces, tirets, apostrophes et points
        if n and not re.fullmatch(r"[a-zA-ZÀ-ÿ .\-']+", n):
            raise ValidationError("Le nom du vétérinaire contient des caractères invalides.")
        return n

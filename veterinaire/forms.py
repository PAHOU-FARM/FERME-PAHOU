# veterinaire/forms.py
from django import forms
from django.core.exceptions import ValidationError, FieldError
from django.utils import timezone
import re

from .models import Veterinaire
from troupeau.models import Troupeau


class VeterinaireForm(forms.ModelForm):
    class Meta:
        model = Veterinaire
        fields = [
            "date_visite",
            "troupeau",
            "nom_veterinaire",
            "motif_de_la_visite",
            "traitement_effectue",
            "recommandations",
            "cout_visite",
            "maladie",
            "vaccination",
            "observations",
        ]
        widgets = {
            "date_visite": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "troupeau": forms.Select(attrs={"class": "form-select"}),
            "nom_veterinaire": forms.TextInput(attrs={"class": "form-control", "maxlength": 100}),
            "motif_de_la_visite": forms.Select(attrs={"class": "form-select"}),
            "traitement_effectue": forms.Select(attrs={"class": "form-select"}),
            "recommandations": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "cout_visite": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "maladie": forms.Select(attrs={"class": "form-select"}),
            "vaccination": forms.Select(attrs={"class": "form-select"}),
            "observations": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
        labels = {
            "date_visite": "Date de visite",
            "troupeau": "Animal (boucle)",
            "nom_veterinaire": "Vétérinaire",
            "motif_de_la_visite": "Motif de la visite",
            "traitement_effectue": "Traitement effectué",
            "recommandations": "Recommandations",
            "cout_visite": "Coût de la visite (FCFA)",
            "maladie": "Maladie liée (optionnel)",
            "vaccination": "Vaccination liée (optionnel)",
            "observations": "Observations",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Proposer par défaut les animaux actifs, triés par boucle
        qs = Troupeau.objects.all().order_by("boucle_ovin")
        try:
            # Filtrer seulement si le champ existe réellement
            if any(f.name == "boucle_active" for f in Troupeau._meta.get_fields()):
                qs = qs.filter(boucle_active=True)
        except FieldError:
            pass

        self.fields["troupeau"].queryset = qs
        self.fields["troupeau"].empty_label = "— Sélectionner un animal —"

        # Libellé lisible dans le select
        def _label_ovin(obj: Troupeau):
            get_sexe = getattr(obj, "get_sexe_display", None)
            sexe = get_sexe() if callable(get_sexe) else getattr(obj, "sexe", "")
            get_race = getattr(obj, "get_race_display", None)
            race = get_race() if callable(get_race) else getattr(obj, "race", "")
            sup = " / ".join(x for x in (sexe, race) if x)
            return f"{obj.boucle_ovin} — {sup}" if sup else f"{obj.boucle_ovin}"

        self.fields["troupeau"].label_from_instance = _label_ovin

        # Maladie / Vaccination optionnels → empty label lisible
        if "maladie" in self.fields:
            self.fields["maladie"].empty_label = "— Aucune —"
        if "vaccination" in self.fields:
            self.fields["vaccination"].empty_label = "— Aucune —"

    # Validations légères côté form (complément des validations modèle)
    def clean_date_visite(self):
        d = self.cleaned_data.get("date_visite")
        if d and d > timezone.localdate():
            raise ValidationError("La date ne peut pas être dans le futur.")
        return d

    def clean_nom_veterinaire(self):
        n = (self.cleaned_data.get("nom_veterinaire") or "").strip()
        # Autoriser lettres, espaces, tirets, apostrophes (avec accents)
        if n and not re.fullmatch(r"[A-Za-zÀ-ÖØ-öø-ÿ \-']+", n):
            raise ValidationError("Le nom du vétérinaire contient des caractères invalides.")
        return n

    def clean_cout_visite(self):
        v = self.cleaned_data.get("cout_visite")
        if v is not None and v < 0:
            raise ValidationError("Le coût doit être positif ou nul.")
        return v

    def clean(self):
        cleaned = super().clean()
        # Pas de contrainte entre maladie/vaccination : on laisse libre.
        return cleaned

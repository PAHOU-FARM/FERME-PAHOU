from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Maladie
from troupeau.models import Troupeau


class MaladieForm(forms.ModelForm):
    class Meta:
        model = Maladie
        fields = [
            "Boucle_Ovin",
            "Nom_Maladie",
            "Symptomes_Observes",
            "Date_observation",
            "Date_guerison",
            "Statut",
            "Gravite",
            "Traitement_Administre",
            "Duree_Traitement",
            "Cout_Traitement_FCFA",
            "Veterinaire",
            "Observations",
        ]
        widgets = {
            "Boucle_Ovin": forms.Select(attrs={"class": "form-select"}),
            "Nom_Maladie": forms.Select(attrs={"class": "form-select"}),
            "Symptomes_Observes": forms.Select(attrs={"class": "form-select"}),
            "Date_observation": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "Date_guerison": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "Statut": forms.Select(attrs={"class": "form-select"}),
            "Gravite": forms.Select(attrs={"class": "form-select"}),
            "Traitement_Administre": forms.Select(attrs={"class": "form-select"}),
            "Duree_Traitement": forms.NumberInput(attrs={"min": "0", "step": "1", "class": "form-control"}),
            "Cout_Traitement_FCFA": forms.NumberInput(attrs={"min": "0", "step": "0.01", "class": "form-control"}),
            "Veterinaire": forms.TextInput(attrs={"class": "form-control"}),
            "Observations": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }
        labels = {
            "Boucle_Ovin": "Boucle Ovin",
            "Nom_Maladie": "Maladie",
            "Symptomes_Observes": "Symptômes observés",
            "Date_observation": "Date d’observation",
            "Date_guerison": "Date de guérison",
            "Statut": "Statut",
            "Gravite": "Gravité",
            "Traitement_Administre": "Traitement administré",
            "Duree_Traitement": "Durée du traitement (jours)",
            "Cout_Traitement_FCFA": "Coût du traitement (FCFA)",
            "Veterinaire": "Vétérinaire",
            "Observations": "Observations",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Propose en priorité les animaux actifs, triés par boucle
        qs = Troupeau.objects.all().order_by("boucle_ovin")
        if hasattr(Troupeau, "boucle_active"):
            qs = qs.filter(boucle_active=True)
        self.fields["Boucle_Ovin"].queryset = qs
        self.fields["Boucle_Ovin"].empty_label = "— Sélectionner un animal —"

        # Label lisible (BOUCLE — sexe/race si disponibles)
        def _label(o):
            parts = [getattr(o, "boucle_ovin", str(o.pk))]
            if hasattr(o, "get_sexe_display"):
                parts.append(o.get_sexe_display())
            if hasattr(o, "get_race_display"):
                parts.append(o.get_race_display())
            return " — ".join(parts)
        self.fields["Boucle_Ovin"].label_from_instance = _label

    # Validations douces côté form (le modèle + signaux font déjà le gros)
    def clean_Date_observation(self):
        d = self.cleaned_data.get("Date_observation")
        if d and d > timezone.localdate():
            raise ValidationError("La date d’observation ne peut pas être dans le futur.")
        return d

    def clean(self):
        cleaned = super().clean()
        d_obs = cleaned.get("Date_observation")
        d_gue = cleaned.get("Date_guerison")
        if d_obs and d_gue and d_gue < d_obs:
            self.add_error("Date_guerison", "La date de guérison doit être postérieure à la date d’observation.")
        cout = cleaned.get("Cout_Traitement_FCFA")
        if cout is not None and cout < 0:
            self.add_error("Cout_Traitement_FCFA", "Le coût du traitement ne peut pas être négatif.")
        return cleaned

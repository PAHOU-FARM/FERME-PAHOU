from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Vente
from troupeau.models import Troupeau


class VenteForm(forms.ModelForm):
    class Meta:
        model = Vente
        fields = [
            "boucle_ovin",
            "date_vente",
            "poids_kg",
            "prix_vente",
            "type_acheteur",
            "proprietaire_ovin",
            "observations",
        ]
        widgets = {
            "boucle_ovin": forms.Select(attrs={"class": "form-select"}),
            "date_vente": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "poids_kg": forms.NumberInput(attrs={"step": "0.01", "min": "0.01", "class": "form-control"}),
            "prix_vente": forms.NumberInput(attrs={"step": "0.01", "min": "0", "class": "form-control"}),
            "type_acheteur": forms.Select(attrs={"class": "form-select"}),
            "proprietaire_ovin": forms.Select(attrs={"class": "form-select"}),
            "observations": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }
        labels = {
            "boucle_ovin": "Boucle Ovin",
            "date_vente": "Date de vente",
            "poids_kg": "Poids (kg)",
            "prix_vente": "Prix de vente",
            "type_acheteur": "Type d’acheteur",
            "proprietaire_ovin": "Propriétaire",
            "observations": "Observations",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Proposer en priorité les animaux actifs (si le champ existe), triés
        qs = Troupeau.objects.all().order_by("boucle_ovin")
        try:
            qs = qs.filter(boucle_active=True)
        except Exception:
            # Si le champ n'existe pas, on ignore le filtre
            pass
        self.fields["boucle_ovin"].queryset = qs
        self.fields["boucle_ovin"].empty_label = "— Sélectionner un animal —"

        # Label lisible pour l'ovin
        def _label(o: Troupeau):
            sexe = getattr(o, "get_sexe_display", lambda: getattr(o, "sexe", ""))()
            race = getattr(o, "get_race_display", lambda: getattr(o, "race", ""))()
            sup = " / ".join([x for x in (sexe, race) if x])
            return f"{o.boucle_ovin} — {sup}" if sup else f"{o.boucle_ovin}"

        self.fields["boucle_ovin"].label_from_instance = _label

    # Validations côté formulaire (en plus de celles du modèle)
    def clean_date_vente(self):
        d = self.cleaned_data.get("date_vente")
        if d and d > timezone.localdate():
            raise ValidationError("La date de vente ne peut pas être dans le futur.")
        # Cohérence simple avec la date de naissance si disponible
        bov = self.cleaned_data.get("boucle_ovin")
        naissance = getattr(bov, "naissance_date", None)
        if d and naissance and d < naissance:
            raise ValidationError("La date de vente ne peut pas précéder la naissance de l’animal.")
        return d

    def clean_poids_kg(self):
        v = self.cleaned_data.get("poids_kg")
        if v is None:
            return v
        if v <= 0:
            raise ValidationError("Le poids doit être strictement positif.")
        return v

    def clean_prix_vente(self):
        v = self.cleaned_data.get("prix_vente")
        if v is None:
            return v
        if v < 0:
            raise ValidationError("Le prix de vente ne peut pas être négatif.")
        return v

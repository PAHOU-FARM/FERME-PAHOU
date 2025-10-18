from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from troupeau.models import Troupeau
from .models import Embouche


class EmboucheForm(forms.ModelForm):
    """Formulaire public (les champs calculés sont exclus)."""

    class Meta:
        model = Embouche
        fields = [
            "boucle_ovin",
            "date_entree",
            "poids_initial",
            "date_fin",
            "poids_fin",
            "proprietaire",
            "sexe",
            "observations",
        ]
        widgets = {
            "boucle_ovin": forms.Select(attrs={"class": "form-select"}),
            "date_entree": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "poids_initial": forms.NumberInput(attrs={"step": "0.1", "min": "0", "class": "form-control"}),
            "date_fin": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "poids_fin": forms.NumberInput(attrs={"step": "0.1", "min": "0", "class": "form-control"}),
            "proprietaire": forms.Select(attrs={"class": "form-select"}),
            "sexe": forms.Select(attrs={"class": "form-select"}),
            "observations": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }
        labels = {
            "boucle_ovin": _("Boucle ovin"),
            "date_entree": _("Date d'entrée"),
            "poids_initial": _("Poids initial (kg)"),
            "date_fin": _("Date de fin"),
            "poids_fin": _("Poids final (kg)"),
            "proprietaire": _("Propriétaire"),
            "sexe": _("Sexe"),
            "observations": _("Observations"),
        }
        help_texts = {
            "poids_initial": _("Utilisez un point comme séparateur décimal."),
            "poids_fin": _("Facultatif — requis seulement si l’embouche est terminée."),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # FK : proposer d’abord les animaux actifs (si le champ existe) et trier par boucle
        qs = Troupeau.objects.all().order_by("boucle_ovin")
        if hasattr(Troupeau, "boucle_active"):
            qs = qs.filter(boucle_active=True)
        self.fields["boucle_ovin"].queryset = qs
        self.fields["boucle_ovin"].empty_label = "— Sélectionner un animal —"

        # Libellé lisible
        def _label(obj: Troupeau):
            sexe = getattr(obj, "get_sexe_display", lambda: obj.sexe)()
            race = getattr(obj, "get_race_display", lambda: obj.race)()
            return f"{obj.boucle_ovin} — {sexe} / {race}"
        self.fields["boucle_ovin"].label_from_instance = _label

    # Validations de confort (le modèle refait les garde-fous).
    def clean(self):
        cleaned = super().clean()
        d_entree = cleaned.get("date_entree")
        d_fin = cleaned.get("date_fin")
        p_init = cleaned.get("poids_initial")
        p_fin = cleaned.get("poids_fin")

        if d_entree and d_fin and d_fin <= d_entree:
            self.add_error("date_fin", _("La date de fin doit être postérieure à la date d'entrée."))

        if p_init is not None and p_fin is not None and p_fin <= p_init:
            self.add_error("poids_fin", _("Le poids final doit être supérieur au poids initial."))

        return cleaned

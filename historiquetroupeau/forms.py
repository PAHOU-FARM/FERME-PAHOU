# historiquetroupeau/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import HistoriqueTroupeau
from troupeau.models import Troupeau


# ---------------------------
# Formulaire principal (CRUD)
# ---------------------------
class HistoriqueTroupeauForm(forms.ModelForm):
    class Meta:
        model = HistoriqueTroupeau
        # Inclure tous les champs pour ne rien oublier. Tu peux restreindre si besoin.
        fields = "__all__"

        # Widgets soignés (Bootstrap) pour les champs les plus courants
        widgets = {
            "troupeau": forms.Select(attrs={"class": "form-select"}),

            "date_evenement": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),

            # Observations en textarea
            "observations": forms.Textarea(
                attrs={"rows": 3, "class": "form-control"}
            ),

            # Anciennes/Nouvelles dates (si présentes dans le modèle)
            "ancienne_naissance_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "nouvelle_naissance_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "ancienne_achat_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "nouvelle_achat_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "ancienne_entree_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "nouvelle_entree_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "ancienne_date_sortie": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "nouvelle_date_sortie": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
        }

        labels = {
            "troupeau": "Animal (optionnel)",
            "date_evenement": "Date de l’événement",
            "statut": "Statut",
            "observations": "Observations",
            "ancienne_boucle": "Ancienne boucle",
            "nouvelle_boucle": "Nouvelle boucle",
        }

        help_texts = {
            "troupeau": "Sélectionne l’animal si l’événement est rattaché.",
            "date_evenement": "La date ne peut pas être dans le futur.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Appliquer un style Bootstrap par défaut aux champs texte/numériques qui n’ont pas de widget personnalisé
        for name, field in self.fields.items():
            if not getattr(field.widget.attrs, "get", None):
                # Pas un widget « attrs » standard : on skip
                continue
            # Ne pas écraser les widgets déjà stylés plus haut
            if "class" not in field.widget.attrs:
                if isinstance(field.widget, (forms.Select, forms.CheckboxInput, forms.RadioSelect)):
                    field.widget.attrs["class"] = "form-select" if isinstance(field.widget, forms.Select) else "form-check-input"
                else:
                    field.widget.attrs["class"] = "form-control"

        # Restreindre la liste déroulante à quelque chose de lisible et ordonné
        if "troupeau" in self.fields:
            qs = (
                Troupeau.objects.all()
                .only("id", "boucle_ovin")
                .order_by("boucle_ovin")
            )
            self.fields["troupeau"].queryset = qs
            self.fields["troupeau"].empty_label = "— Aucun (événement générique) —"

    # --------- Validations ciblées ---------

    def clean_date_evenement(self):
        d = self.cleaned_data.get("date_evenement")
        if not d:
            return d
        today = getattr(timezone, "localdate", lambda: timezone.now().date())()
        if d > today:
            raise ValidationError("La date de l’événement ne peut pas être dans le futur.")
        return d

    def clean(self):
        """
        Validation globale légère :
        - si aucun animal n’est sélectionné, on recommande d’avoir au moins une info (ancienne/nouvelle boucle).
        """
        cleaned = super().clean()
        troupeau = cleaned.get("troupeau")
        ancienne = cleaned.get("ancienne_boucle")
        nouvelle = cleaned.get("nouvelle_boucle")

        if not troupeau and not (ancienne or nouvelle):
            self.add_error(
                "nouvelle_boucle",
                "Indique au moins une boucle (ancienne ou nouvelle) si aucun animal n’est sélectionné."
            )
        return cleaned


# -----------------------------------
# Formulaire de filtres pour la liste
# -----------------------------------
class HistoriqueFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="Recherche",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "boucle, statut, observations..."}),
    )
    statut = forms.CharField(
        required=False,
        label="Statut",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "ex: Modification"}),
    )
    from_date = forms.DateField(
        required=False,
        label="Du",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    to_date = forms.DateField(
        required=False,
        label="Au",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    troupeau_id = forms.IntegerField(
        required=False,
        label="ID Troupeau",
        widget=forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
    )

    def clean(self):
        cleaned = super().clean()
        d1 = cleaned.get("from_date")
        d2 = cleaned.get("to_date")
        if d1 and d2 and d1 > d2:
            self.add_error("to_date", "La date de fin doit être postérieure à la date de début.")
        return cleaned

    def query_params(self):
        """
        Utile pour reconstruire l’URL de pagination en conservant les filtres.
        Retourne un dict avec les noms attendus par tes vues/templates.
        """
        cd = self.cleaned_data if self.is_valid() else {}
        return {
            "q": cd.get("q") or "",
            "statut": cd.get("statut") or "",
            "from": (cd.get("from_date") or "") and cd.get("from_date").isoformat(),
            "to": (cd.get("to_date") or "") and cd.get("to_date").isoformat(),
            "troupeau_id": cd.get("troupeau_id") or "",
        }

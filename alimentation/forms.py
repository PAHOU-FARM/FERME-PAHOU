from django import forms
from django.core.exceptions import ValidationError, FieldDoesNotExist
from django.utils import timezone

from .models import Alimentation
from troupeau.models import Troupeau


class AlimentationForm(forms.ModelForm):
    class Meta:
        model = Alimentation
        fields = [
            "Boucle_Ovin",
            "Date_alimentation",
            "Type_Aliment",
            "Quantite_Kg",
            "Objectif",
            "Observations",
        ]
        widgets = {
            "Boucle_Ovin": forms.Select(attrs={"class": "form-select"}),
            "Date_alimentation": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "Type_Aliment": forms.Select(attrs={"class": "form-select"}),
            "Quantite_Kg": forms.NumberInput(attrs={"step": "0.01", "class": "form-control", "min": "0"}),
            "Objectif": forms.Select(attrs={"class": "form-select"}),
            "Observations": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }
        labels = {
            "Boucle_Ovin": "Boucle Ovin",
            "Date_alimentation": "Date d’alimentation",
            "Type_Aliment": "Type d’aliment",
            "Quantite_Kg": "Quantité (kg)",
            "Objectif": "Objectif",
            "Observations": "Observations",
        }
        help_texts = {
            "Quantite_Kg": "Utilisez un point comme séparateur décimal (ex : 2.5).",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Sécuriser l’accès au champ (si le modèle change, on évite une KeyError)
        if "Boucle_Ovin" in self.fields:
            qs = Troupeau.objects.all().order_by("boucle_ovin")

            # Filtrer sur boucle_active si le champ existe
            try:
                Troupeau._meta.get_field("boucle_active")
                qs = qs.filter(boucle_active=True)
            except FieldDoesNotExist:
                pass

            self.fields["Boucle_Ovin"].queryset = qs
            self.fields["Boucle_Ovin"].empty_label = "— Sélectionner un animal —"

            # Libellé lisible (boucle — sexe / race) si ces champs existent
            def _label(obj):
                label = f"{getattr(obj, 'boucle_ovin', obj.pk)}"
                parts = []
                # Afficher displays uniquement si choices définies
                try:
                    parts.append(obj.get_sexe_display())
                except Exception:
                    if hasattr(obj, "sexe"):
                        parts.append(str(obj.sexe))
                try:
                    parts.append(obj.get_race_display())
                except Exception:
                    if hasattr(obj, "race"):
                        parts.append(str(obj.race))
                parts = [p for p in parts if p and p != "None"]
                if parts:
                    label += " — " + " / ".join(parts)
                return label

            self.fields["Boucle_Ovin"].label_from_instance = _label

        # Valeur par défaut : aujourd’hui si non fourni (coté widget)
        if not self.is_bound and "Date_alimentation" in self.fields and not getattr(self.instance, "Date_alimentation", None):
            try:
                self.fields["Date_alimentation"].initial = timezone.localdate()
            except Exception:
                self.fields["Date_alimentation"].initial = timezone.now().date()

    # ------- Validations champ par champ -------

    def clean_Date_alimentation(self):
        d = self.cleaned_data.get("Date_alimentation")
        today = getattr(timezone, "localdate", lambda: timezone.now().date())()
        if d and d > today:
            raise ValidationError("La date ne peut pas être dans le futur.")

        # Cohérence simple : pas avant la naissance de l’animal (si dispo)
        bov = self.cleaned_data.get("Boucle_Ovin")
        if d and bov and getattr(bov, "naissance_date", None) and d < bov.naissance_date:
            raise ValidationError("La date d’alimentation ne peut pas être antérieure à la naissance de l’animal.")
        return d

    def clean_Quantite_Kg(self):
        q = self.cleaned_data.get("Quantite_Kg")
        if q is None:
            return q  # laisser la validation 'required' décider si nécessaire
        if q <= 0:
            raise ValidationError("La quantité doit être strictement positive.")
        return q

    # ------- Validation globale -------

    def clean(self):
        """
        Validation globale légère : prévenir le doublon (Boucle + Date)
        en amont de la contrainte unique en base (le cas échéant).
        """
        cleaned = super().clean()
        bov = cleaned.get("Boucle_Ovin")
        d = cleaned.get("Date_alimentation")
        current_pk = getattr(self.instance, "pk", None)

        if bov and d:
            exists = (
                Alimentation.objects
                .filter(Boucle_Ovin=bov, Date_alimentation=d)
                .exclude(pk=current_pk)
                .exists()
            )
            if exists:
                self.add_error(
                    "Date_alimentation",
                    "Un enregistrement d’alimentation existe déjà pour cet ovin à cette date."
                )
        return cleaned

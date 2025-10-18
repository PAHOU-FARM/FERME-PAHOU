from django import forms
from django.core.exceptions import ValidationError

from .models import Genealogie
from troupeau.models import Troupeau


class GenealogieForm(forms.ModelForm):
    class Meta:
        model = Genealogie
        fields = ["agneau", "mere", "pere"]
        labels = {
            "agneau": "Agneau (boucle)",
            "mere": "Mère (boucle)",
            "pere": "Père (boucle)",
        }
        widgets = {
            "agneau": forms.Select(attrs={"class": "form-select"}),
            "mere": forms.Select(attrs={"class": "form-select"}),
            "pere": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        base_qs = Troupeau.objects.all().order_by("boucle_ovin")
        self.fields["agneau"].queryset = base_qs
        self.fields["pere"].queryset = base_qs.filter(sexe="male", boucle_active=True)
        self.fields["mere"].queryset = base_qs.filter(sexe="femelle", boucle_active=True)

        self.fields["agneau"].empty_label = "— Sélectionner l’agneau —"
        self.fields["pere"].empty_label = "— Sélectionner le père —"
        self.fields["mere"].empty_label = "— Sélectionner la mère —"

        # Affichage lisible dans les listes
        def _label(obj):
            sexe = getattr(obj, "get_sexe_display", lambda: obj.sexe)()
            race = getattr(obj, "get_race_display", lambda: obj.race)()
            return f"{obj.boucle_ovin} — {sexe} / {race}"

        self.fields["agneau"].label_from_instance = _label
        self.fields["pere"].label_from_instance = _label
        self.fields["mere"].label_from_instance = _label

    def clean(self):
        cleaned = super().clean()
        agneau = cleaned.get("agneau")
        pere = cleaned.get("pere")
        mere = cleaned.get("mere")

        errors = {}

        if agneau and pere and agneau == pere:
            errors["pere"] = "L’agneau ne peut pas être son propre père."
        if agneau and mere and agneau == mere:
            errors["mere"] = "L’agneau ne peut pas être sa propre mère."
        if pere and mere and pere == mere:
            errors["mere"] = "Le père et la mère doivent être différents."

        # Sécurité supplémentaire (au-delà du filtrage queryset)
        if pere and pere.sexe != "male":
            errors["pere"] = "Le père doit être de sexe masculin."
        if mere and mere.sexe != "femelle":
            errors["mere"] = "La mère doit être de sexe féminin."
        if pere and not pere.boucle_active:
            errors["pere"] = "Le père doit être un animal actif."
        if mere and not mere.boucle_active:
            errors["mere"] = "La mère doit être un animal actif."

        # Éviter les doublons OneToOne (message amont, même si la contrainte DB existe)
        if agneau:
            qs = Genealogie.objects.filter(agneau=agneau)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                errors["agneau"] = "Une généalogie existe déjà pour cet agneau."

        if errors:
            raise ValidationError(errors)
        return cleaned

# naissance/forms.py
from django import forms
from django.core.exceptions import ValidationError

from .models import Naissance, Agneau
from troupeau.models import Troupeau
from accouplement.models import Accouplement


class NaissanceForm(forms.ModelForm):
    class Meta:
        model = Naissance
        fields = [
            "boucle_mere",
            "date_mise_bas",
            "origine_accouplement",
            "accouplement",
            "nom_male_externe",
            "observations",
        ]
        widgets = {
            "boucle_mere": forms.Select(attrs={"class": "form-select"}),
            "date_mise_bas": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "origine_accouplement": forms.Select(attrs={"class": "form-select"}),
            "accouplement": forms.Select(attrs={"class": "form-select"}),
            "nom_male_externe": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Nom/boucle du mâle externe",
            }),
            "observations": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
        labels = {
            "boucle_mere": "Mère (boucle)",
            "date_mise_bas": "Date de mise-bas",
            "origine_accouplement": "Origine de l'accouplement",
            "accouplement": "Accouplement (si interne)",
            "nom_male_externe": "Mâle externe (si externe)",
            "observations": "Observations",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Femelles actives uniquement, triées
        self.fields["boucle_mere"].queryset = (
            Troupeau.objects.filter(sexe="femelle", boucle_active=True).order_by("boucle_ovin")
        )
        self.fields["boucle_mere"].empty_label = "— Sélectionner —"
        self.fields["boucle_mere"].label_from_instance = (
            lambda o: f"{o.boucle_ovin} — {getattr(o, 'race', '') or getattr(o, 'get_race_display', lambda: '')()}"
        )

        # Accouplements, restreints à la mère si connue
        acc_qs = Accouplement.objects.select_related("boucle_brebis", "boucle_belier").order_by("-date_debut_lutte")
        mother_id = self.data.get("boucle_mere") or getattr(self.instance, "boucle_mere_id", None)
        if mother_id:
            try:
                acc_qs = acc_qs.filter(boucle_brebis_id=int(mother_id))
            except (TypeError, ValueError):
                pass
        self.fields["accouplement"].queryset = acc_qs
        self.fields["accouplement"].required = False
        self.fields["accouplement"].empty_label = "— (si Interne) —"

        # Champ mâle externe non requis par défaut (dépend de l'origine)
        self.fields["nom_male_externe"].required = False

    def clean(self):
        cleaned = super().clean()
        origine = cleaned.get("origine_accouplement")
        acc = cleaned.get("accouplement")
        male_ext = (cleaned.get("nom_male_externe") or "").strip()
        mere = cleaned.get("boucle_mere")
        dmb = cleaned.get("date_mise_bas")

        # Règles d'exclusivité / obligation
        if origine == "Interne":
            if not acc:
                self.add_error("accouplement", "Pour un accouplement interne, sélectionnez l’enregistrement d’accouplement.")
            # Si interne, on ignore le champ mâle externe
            cleaned["nom_male_externe"] = ""
        elif origine == "Externe":
            if not male_ext:
                self.add_error("nom_male_externe", "Pour un accouplement externe, indiquez le mâle utilisé.")
            # Si externe, on ignore l'accouplement interne
            cleaned["accouplement"] = None
        else:
            # Inconnu : ne pas avoir les deux champs renseignés
            if acc and male_ext:
                raise ValidationError("Un accouplement ne peut pas être à la fois interne et externe.")

        # Cohérence mère / accouplement
        if acc and mere and acc.boucle_brebis_id != mere.id:
            self.add_error("accouplement", "L’accouplement choisi n’appartient pas à cette mère.")

        # Cohérence temporelle (si interne)
        if acc and dmb and acc.date_debut_lutte and dmb < acc.date_debut_lutte:
            self.add_error("date_mise_bas", "La mise-bas ne peut pas être antérieure au début de lutte.")

        return cleaned


class AgneauForm(forms.ModelForm):
    class Meta:
        model = Agneau
        fields = ["naissance", "boucle", "sexe"]
        widgets = {
            "naissance": forms.Select(attrs={"class": "form-select"}),
            "boucle": forms.Select(attrs={"class": "form-select"}),
            "sexe": forms.Select(attrs={"class": "form-select"}),
        }
        labels = {
            "naissance": "Naissance",
            "boucle": "Boucle de l’agneau",
            "sexe": "Sexe",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Naissance (liste la plus récente en premier)
        self.fields["naissance"].queryset = Naissance.objects.select_related("boucle_mere").order_by("-date_mise_bas", "-id")
        self.fields["naissance"].empty_label = "— Sélectionner —"

        # Par défaut : ovins au statut "naissance" (adapter si ton modèle utilise une autre valeur)
        qs = Troupeau.objects.filter(statut="naissance").order_by("boucle_ovin")
        self.fields["boucle"].queryset = qs
        self.fields["boucle"].empty_label = "— Sélectionner —"
        self.fields["boucle"].label_from_instance = (
            lambda o: f"{o.boucle_ovin} — {getattr(o, 'get_sexe_display', lambda: '')()} / {getattr(o, 'get_race_display', lambda: '')()}"
        )

        # Si une naissance est choisie, on peut restreindre aux agneaux de cette mère (si le modèle Troupeau a mere_boucle)
        naissance_id = self.data.get("naissance") or getattr(self.instance, "naissance_id", None)
        if naissance_id:
            try:
                n = Naissance.objects.select_related("boucle_mere").get(pk=int(naissance_id))
                if hasattr(Troupeau, "mere_boucle"):
                    self.fields["boucle"].queryset = qs.filter(mere_boucle=n.boucle_mere)
            except (Naissance.DoesNotExist, ValueError, TypeError):
                pass

    def clean(self):
        cleaned = super().clean()
        n = cleaned.get("naissance")
        b = cleaned.get("boucle")

        if not n or not b:
            return cleaned

        # Vérifier cohérence mère si l’info existe sur le modèle Troupeau
        if hasattr(b, "mere_boucle_id") and b.mere_boucle_id and n.boucle_mere_id:
            if b.mere_boucle_id != n.boucle_mere_id:
                self.add_error("boucle", "La mère de la boucle sélectionnée ne correspond pas à la mère de cette naissance.")

        # Vérifier le statut "naissance" de la boucle (adapter la valeur au besoin)
        if getattr(b, "statut", None) != "naissance":
            self.add_error("boucle", "La boucle choisie n’est pas marquée comme 'Naissance' dans le troupeau.")

        return cleaned

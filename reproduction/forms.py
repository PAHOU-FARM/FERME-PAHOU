from django import forms
from django.core.exceptions import ValidationError

from .models import Reproduction
from troupeau.models import Troupeau
from accouplement.models import Accouplement
from gestation.models import Gestation
from naissance.models import Naissance


class ReproductionForm(forms.ModelForm):
    class Meta:
        model = Reproduction
        fields = ["femelle", "male", "accouplement", "gestation", "naissance", "observations"]
        widgets = {
            "femelle": forms.Select(attrs={"class": "form-select"}),
            "male": forms.Select(attrs={"class": "form-select"}),
            "accouplement": forms.Select(attrs={"class": "form-select"}),
            "gestation": forms.Select(attrs={"class": "form-select"}),
            "naissance": forms.Select(attrs={"class": "form-select"}),
            "observations": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }
        labels = {
            "femelle": "Femelle (brebis)",
            "male": "Mâle (bélier)",
            "accouplement": "Accouplement",
            "gestation": "Gestation (optionnel)",
            "naissance": "Naissance (optionnel)",
            "observations": "Observations",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Limiter les choix sur Troupeau (cohérent avec ton modèle)
        self.fields["femelle"].queryset = Troupeau.objects.filter(sexe="femelle", boucle_active=True).order_by("boucle_ovin")
        self.fields["male"].queryset = Troupeau.objects.filter(sexe="male", boucle_active=True).order_by("boucle_ovin")

        # Affichage lisible des animaux
        def _label_troupeau(t: Troupeau):
            try:
                sexe = t.get_sexe_display()
                race = t.get_race_display()
            except Exception:
                sexe, race = t.sexe, t.race
            return f"{t.boucle_ovin} — {sexe}/{race}"

        self.fields["femelle"].label_from_instance = _label_troupeau
        self.fields["male"].label_from_instance = _label_troupeau

        # Choix des autres FK
        self.fields["accouplement"].queryset = (
            Accouplement.objects.select_related("boucle_brebis", "boucle_belier").order_by("-date_debut_lutte")
        )
        self.fields["gestation"].queryset = (
            Gestation.objects.select_related("boucle_brebis").order_by("-date_gestation")
        )
        self.fields["naissance"].queryset = (
            Naissance.objects.select_related("boucle_mere").order_by("-date_mise_bas")
        )

        # Labels lisibles
        self.fields["accouplement"].label_from_instance = lambda a: (
            f"{a.boucle_brebis.boucle_ovin} × {a.boucle_belier.boucle_ovin} — {a.date_debut_lutte:%d/%m/%Y}"
        )
        self.fields["gestation"].label_from_instance = lambda g: (
            f"{g.boucle_brebis.boucle_ovin} — {g.get_etat_gestation_display()} ({g.date_gestation:%d/%m/%Y})"
        )
        self.fields["naissance"].label_from_instance = lambda n: (
            f"{n.boucle_mere.boucle_ovin} — {n.date_mise_bas:%d/%m/%Y}"
        )

    def clean(self):
        cleaned = super().clean()
        femelle = cleaned.get("femelle")
        male = cleaned.get("male")
        acc = cleaned.get("accouplement")

        # Cohérence douce avec l'accouplement (la validation forte est dans model.clean)
        if acc:
            if femelle and acc.boucle_brebis_id != femelle.id:
                raise ValidationError({"femelle": "La femelle ne correspond pas à celle de l'accouplement."})
            if male and acc.boucle_belier_id != male.id:
                raise ValidationError({"male": "Le mâle ne correspond pas à celui de l'accouplement."})

        return cleaned

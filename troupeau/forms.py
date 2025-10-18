from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Troupeau


class TroupeauForm(forms.ModelForm):
    """Formulaire pour créer/modifier un animal du troupeau"""

    class Meta:
        model = Troupeau
        fields = [
            'boucle_ovin', 'sexe', 'race', 'naissance_date',
            'poids_initial', 'taille_initiale', 'pere_boucle', 'mere_boucle',
            'achat_date', 'entree_date', 'date_sortie', 'statut',
            'origine_ovin', 'proprietaire_ovin', 'observations', 'boucle_active'
        ]
        widgets = {
            'boucle_ovin': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: OV001'
            }),
            'sexe': forms.Select(attrs={'class': 'form-control'}),
            'race': forms.Select(attrs={'class': 'form-control'}),
            'naissance_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'poids_initial': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0'
            }),
            'taille_initiale': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0'
            }),
            # Laisse Django générer l'id (id_for_label restera correct)
            'pere_boucle': forms.Select(attrs={'class': 'form-control'}),
            'mere_boucle': forms.Select(attrs={'class': 'form-control'}),
            'achat_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'entree_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'date_sortie': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'statut': forms.Select(attrs={'class': 'form-control'}),
            'origine_ovin': forms.Select(attrs={'class': 'form-control'}),
            'proprietaire_ovin': forms.Select(attrs={'class': 'form-control'}),
            'observations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': "Notes et observations sur l'animal..."
            }),
            'boucle_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'boucle_ovin': _('Numéro de boucle'),
            'sexe': _('Sexe'),
            'race': _('Race'),
            'naissance_date': _('Date de naissance'),
            'poids_initial': _('Poids initial (kg)'),
            'taille_initiale': _('Taille initiale (cm)'),
            'pere_boucle': _('Père'),
            'mere_boucle': _('Mère'),
            'achat_date': _("Date d'achat"),
            'entree_date': _("Date d'entrée"),
            'date_sortie': _('Date de sortie'),
            'statut': _('Statut'),
            'origine_ovin': _('Origine'),
            'proprietaire_ovin': _('Propriétaire'),
            'observations': _('Observations'),
            'boucle_active': _('Boucle active'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Limiter les choix des parents (dynamiques + exclure soi-même en édition)
        males = Troupeau.objects.filter(sexe='male', boucle_active=True).order_by('boucle_ovin')
        femelles = Troupeau.objects.filter(sexe='femelle', boucle_active=True).order_by('boucle_ovin')
        if self.instance and self.instance.pk:
            males = males.exclude(pk=self.instance.pk)
            femelles = femelles.exclude(pk=self.instance.pk)

        field_pere = self.fields.get('pere_boucle')
        if isinstance(field_pere, forms.ModelChoiceField):
            field_pere.queryset = males
            field_pere.empty_label = "Sélectionner un père"

        field_mere = self.fields.get('mere_boucle')
        if isinstance(field_mere, forms.ModelChoiceField):
            field_mere.queryset = femelles
            field_mere.empty_label = "Sélectionner une mère"

        # Marquer certains champs obligatoires (affiche un * dans le label)
        required_fields = ['boucle_ovin', 'sexe', 'race', 'statut', 'origine_ovin', 'proprietaire_ovin']
        for name in required_fields:
            if name in self.fields:
                self.fields[name].required = True
                lbl = self.fields[name].label or name
                self.fields[name].label = f"{lbl} *"

    def clean_boucle_ovin(self):
        # Nettoyage simple : trim + garder la casse telle quelle (ou upper() si tu préfères)
        val = (self.cleaned_data.get('boucle_ovin') or '').strip()
        if not val:
            raise ValidationError(_("Le numéro de boucle est obligatoire."))
        return val

    def clean(self):
        """Validation personnalisée du formulaire"""
        cleaned = super().clean()

        pere = cleaned.get('pere_boucle')
        mere = cleaned.get('mere_boucle')
        naissance = cleaned.get('naissance_date')
        sexe = cleaned.get('sexe')

        # Parents du bon sexe
        if pere and pere.sexe != 'male':
            self.add_error('pere_boucle', _("Le père doit être un animal de sexe masculin."))
        if mere and mere.sexe != 'femelle':
            self.add_error('mere_boucle', _("La mère doit être un animal de sexe féminin."))

        # Âge mini des parents à la naissance
        if naissance:
            if pere and pere.naissance_date:
                age_p_mois = (naissance.year - pere.naissance_date.year) * 12 + (naissance.month - pere.naissance_date.month)
                if naissance.day < pere.naissance_date.day:
                    age_p_mois -= 1
                if age_p_mois < 8:
                    self.add_error('pere_boucle', _("Le père doit avoir au moins 8 mois à la naissance de l'agneau."))

            if mere and mere.naissance_date:
                age_m_mois = (naissance.year - mere.naissance_date.year) * 12 + (naissance.month - mere.naissance_date.month)
                if naissance.day < mere.naissance_date.day:
                    age_m_mois -= 1
                if age_m_mois < 10:
                    self.add_error('mere_boucle', _("La mère doit avoir au moins 10 mois à la naissance de l'agneau."))

        # Poids / taille positifs (si fournis)
        poids = cleaned.get('poids_initial')
        if poids is not None and poids <= 0:
            self.add_error('poids_initial', _("Le poids doit être positif."))

        taille = cleaned.get('taille_initiale')
        if taille is not None and taille <= 0:
            self.add_error('taille_initiale', _("La taille doit être positive."))

        # Alerte non bloquante sur la consanguinité
        if pere and mere:
            temp = Troupeau(
                pere_boucle=pere,
                mere_boucle=mere,
                sexe=sexe or 'male',
                race=cleaned.get('race', 'bali_bali'),
                statut=cleaned.get('statut', 'naissance'),
                origine_ovin=cleaned.get('origine_ovin', 'cotonou'),
                proprietaire_ovin=cleaned.get('proprietaire_ovin', 'miguel'),
            )
            try:
                coeff = temp.coefficient_consanguinite_wright()
                if coeff > 0.125:  # > 12.5%
                    self.add_error(None, _(
                        f"Attention : Le coefficient de consanguinité calculé est de {coeff:.3%}. "
                        f"Un taux élevé peut affecter la santé de la descendance."
                    ))
            except Exception:
                pass

        return cleaned

    def save(self, commit=True):
        """Sauvegarde personnalisée (cohérente avec le modèle)"""
        instance = super().save(commit=False)
        # Harmoniser boucle_active avec le statut (même logique que le modèle)
        if instance.statut in ['vendu', 'decede', 'sortie']:
            instance.boucle_active = False
        if commit:
            instance.save()
        return instance


class TroupeauSearchForm(forms.Form):
    """Formulaire de recherche et filtrage pour la liste des animaux"""

    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par boucle, race ou origine...'
        }),
        label='Recherche'
    )

    statut = forms.ChoiceField(
        choices=[('', 'Tous les statuts')] + Troupeau.STATUT_CHOIX,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Statut'
    )

    sexe = forms.ChoiceField(
        choices=[('', 'Tous les sexes')] + Troupeau.SEXE_CHOIX,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Sexe'
    )

    race = forms.ChoiceField(
        choices=[('', 'Toutes les races')] + Troupeau.RACE_CHOIX,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Race'
    )

    actif_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Animaux actifs uniquement'
    )


class ParentaliteForm(forms.Form):
    """Formulaire pour établir ou modifier les liens de parenté"""

    animal = forms.ModelChoiceField(
        queryset=Troupeau.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Animal'
    )
    pere = forms.ModelChoiceField(
        queryset=Troupeau.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Sélectionner un père",
        label='Père'
    )
    mere = forms.ModelChoiceField(
        queryset=Troupeau.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Sélectionner une mère",
        label='Mère'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # QuerySets dynamiques
        self.fields['animal'].queryset = Troupeau.objects.all().order_by('boucle_ovin')
        self.fields['pere'].queryset = Troupeau.objects.filter(sexe='male', boucle_active=True).order_by('boucle_ovin')
        self.fields['mere'].queryset = Troupeau.objects.filter(sexe='femelle', boucle_active=True).order_by('boucle_ovin')

    def clean(self):
        cleaned = super().clean()
        animal = cleaned.get('animal')
        pere = cleaned.get('pere')
        mere = cleaned.get('mere')

        if animal:
            if animal == pere:
                self.add_error('pere', _("Un animal ne peut pas être son propre père."))
            if animal == mere:
                self.add_error('mere', _("Un animal ne peut pas être sa propre mère."))
            if pere and mere and pere == mere:
                self.add_error('mere', _("Le père et la mère ne peuvent pas être le même animal."))

        return cleaned

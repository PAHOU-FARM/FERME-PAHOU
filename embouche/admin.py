from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Embouche
from troupeau.models import Troupeau


# ---- Filtres personnalisés ----

class RaceOvinFilter(admin.SimpleListFilter):
    title = _('Race')
    parameter_name = 'race'

    def lookups(self, request, model_admin):
        # Récupère les codes de race distincts puis mappe vers le label
        mapping = dict(Troupeau.RACE_CHOIX)
        races = (
            model_admin.get_queryset(request)
            .values_list('boucle_ovin__race', flat=True)
            .distinct()
        )
        return [(code, mapping.get(code, code)) for code in races if code]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(boucle_ovin__race=self.value())
        return queryset


class PoidsEngraissementFilter(admin.SimpleListFilter):
    title = _('Poids engraissement')
    parameter_name = 'poids_engraissement'

    def lookups(self, request, model_admin):
        return [
            ('<10', 'Moins de 10 kg'),
            ('10-20', 'Entre 10 et 20 kg'),
            ('>20', 'Plus de 20 kg'),
        ]

    def queryset(self, request, queryset):
        v = self.value()
        if v == '<10':
            return queryset.filter(poids_engraissement__lt=10)
        if v == '10-20':
            return queryset.filter(poids_engraissement__gte=10, poids_engraissement__lte=20)
        if v == '>20':
            return queryset.filter(poids_engraissement__gt=20)
        return queryset


# ---- Admin ----

@admin.register(Embouche)
class EmboucheAdmin(admin.ModelAdmin):
    list_display = (
        'boucle_ovin',
        'race_ovin',
        'sexe_ovin',
        'age_ovin_embouche',
        'date_entree',
        'date_fin',
        'duree',
        'poids_initial_fmt',
        'poids_fin_fmt',
        'poids_engraissement_fmt',
        'proprietaire_label',
    )
    list_filter = (
        'proprietaire',         # choix alignés au modèle Troupeau
        'sexe',                 # idem
        ('date_entree', admin.DateFieldListFilter),
        ('date_fin', admin.DateFieldListFilter),
        RaceOvinFilter,
        PoidsEngraissementFilter,
    )
    search_fields = ('boucle_ovin__boucle_ovin', 'observations')
    readonly_fields = ('duree', 'poids_engraissement')
    ordering = ['-date_entree', '-id']
    list_per_page = 25

    # Optimisations et confort
    list_select_related = ('boucle_ovin',)
    autocomplete_fields = ('boucle_ovin',)

    # --- Colonnes dérivées & formatées ---

    @admin.display(description='Race', ordering='boucle_ovin__race')
    def race_ovin(self, obj):
        # Label lisible depuis la FK Troupeau
        try:
            return obj.boucle_ovin.get_race_display()
        except Exception:
            return getattr(obj.boucle_ovin, 'race', '—')

    @admin.display(description='Sexe', ordering='boucle_ovin__sexe')
    def sexe_ovin(self, obj):
        try:
            return obj.boucle_ovin.get_sexe_display()
        except Exception:
            return getattr(obj.boucle_ovin, 'sexe', '—')

    @admin.display(description="Âge à l'embouche", ordering='date_entree')
    def age_ovin_embouche(self, obj):
        # Utilise la propriété du modèle (âge en mois au moment de l'entrée)
        age_m = obj.age
        if age_m is None:
            return "Inconnu"
        if age_m < 12:
            return f"{age_m} mois"
        years = age_m // 12
        return f"{years} an{'s' if years > 1 else ''}"

    @admin.display(description="Poids initial (kg)", ordering='poids_initial')
    def poids_initial_fmt(self, obj):
        return f"{obj.poids_initial:.2f}" if obj.poids_initial is not None else "—"

    @admin.display(description="Poids final (kg)", ordering='poids_fin')
    def poids_fin_fmt(self, obj):
        return f"{obj.poids_fin:.2f}" if obj.poids_fin is not None else "—"

    @admin.display(description="Engraissement (kg)", ordering='poids_engraissement')
    def poids_engraissement_fmt(self, obj):
        return f"{obj.poids_engraissement:.2f}" if obj.poids_engraissement is not None else "—"

    @admin.display(description="Propriétaire", ordering='proprietaire')
    def proprietaire_label(self, obj):
        # Affiche le label (pas la valeur brute)
        try:
            return obj.get_proprietaire_display()
        except Exception:
            return obj.proprietaire or '—'

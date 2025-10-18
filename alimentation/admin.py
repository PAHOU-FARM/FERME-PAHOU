from django.contrib import admin
from django.utils.html import format_html
from .models import Alimentation


@admin.register(Alimentation)
class AlimentationAdmin(admin.ModelAdmin):
    # Affichage liste
    list_display = ('Boucle_Ovin', 'Date_alimentation', 'Type_Aliment', 'quantite_kg_fmt', 'Objectif')
    list_display_links = ('Boucle_Ovin', 'Date_alimentation')
    list_filter = ('Type_Aliment', 'Objectif', 'Date_alimentation')
    search_fields = ('Boucle_Ovin__boucle_ovin', 'Observations')
    date_hierarchy = 'Date_alimentation'
    ordering = ('-Date_alimentation',)
    list_per_page = 25

    # Formulaire
    fieldsets = (
        (None, {
            'fields': ('Boucle_Ovin', 'Date_alimentation', 'Type_Aliment', 'Quantite_Kg', 'Objectif', 'Observations')
        }),
    )

    # ✅ Optimisations / confort
    list_select_related = ('Boucle_Ovin',)
    autocomplete_fields = ('Boucle_Ovin',)
    empty_value_display = '—'

    @admin.display(description="Quantité", ordering='Quantite_Kg')
    def quantite_kg_fmt(self, obj):
        if obj.Quantite_Kg is None:
            return "—"
        # Affiche 2 décimales + suffixe kg
        return format_html("{}&nbsp;kg", f"{obj.Quantite_Kg:.2f}")

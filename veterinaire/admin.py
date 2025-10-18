from django.contrib import admin
from django.utils.html import format_html
from .models import Veterinaire


@admin.register(Veterinaire)
class VeterinaireAdmin(admin.ModelAdmin):
    list_display = (
        'date_visite',
        'troupeau_display',
        'sexe_badge',
        'nom_veterinaire',
        'motif_de_la_visite',
        'traitement_effectue',
        'cout_formatee',
    )
    list_filter = (
        'date_visite',
        'motif_de_la_visite',
        'traitement_effectue',
        'troupeau__sexe',
    )
    search_fields = (
        'troupeau__boucle_ovin',
        'nom_veterinaire',
        'motif_de_la_visite',
        'traitement_effectue',
    )
    ordering = ('-date_visite',)
    date_hierarchy = 'date_visite'
    list_select_related = ('troupeau', 'maladie', 'vaccination')
    autocomplete_fields = ('troupeau', 'maladie', 'vaccination')

    @admin.display(description="Animal", ordering='troupeau__boucle_ovin')
    def troupeau_display(self, obj):
        # Affiche le n° de boucle si dispo
        return getattr(obj.troupeau, 'boucle_ovin', str(obj.troupeau) if obj.troupeau else "—")

    @admin.display(description="Sexe", ordering='troupeau__sexe')
    def sexe_badge(self, obj):
        # Utilise la valeur brute pour la couleur, et le display pour le label
        sexe = getattr(obj.troupeau, 'sexe', None)
        label = obj.troupeau.get_sexe_display() if getattr(obj.troupeau, 'get_sexe_display', None) else (sexe or "—")
        color = 'blue' if sexe == 'male' else ('deeppink' if sexe == 'femelle' else 'gray')
        return format_html(
            '<span style="color:#fff;background-color:{};padding:2px 6px;border-radius:6px;">{}</span>',
            color,
            label
        )

    @admin.display(description="Coût", ordering='cout_visite')
    def cout_formatee(self, obj):
        try:
            return f"{obj.cout_visite:.2f}"
        except Exception:
            return obj.cout_visite

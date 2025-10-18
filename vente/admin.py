from django.contrib import admin
from django.utils.html import format_html
from .models import Vente


@admin.register(Vente)
class VenteAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'boucle_ovin',
        'date_vente',
        'poids_kg',
        'prix_vente',
        'type_acheteur',
        'colored_proprietaire',
    )
    list_filter = (
        'type_acheteur',
        'proprietaire_ovin',
        ('date_vente', admin.DateFieldListFilter),
    )
    search_fields = (
        'boucle_ovin__boucle_ovin',   # <-- champ correct du modèle Troupeau
        'type_acheteur',
        'proprietaire_ovin',
    )
    readonly_fields = ('id',)
    ordering = ('-date_vente',)

    # Confort & perf
    list_select_related = ('boucle_ovin',)
    autocomplete_fields = ('boucle_ovin',)

    @admin.display(description='Propriétaire')
    def colored_proprietaire(self, obj):
        color = {
            'Miguel': '#198754',   # vert bootstrap
            'Virgile': '#0d6efd',  # bleu bootstrap
        }.get(obj.proprietaire_ovin, '#6c757d')
        return format_html(
            '<span style="color:#fff;background-color:{};padding:2px 6px;border-radius:6px;">{}</span>',
            color,
            obj.proprietaire_ovin
        )

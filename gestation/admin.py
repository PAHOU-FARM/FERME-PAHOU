from django.contrib import admin
from .models import Gestation


@admin.register(Gestation)
class GestationAdmin(admin.ModelAdmin):
    # Liste
    list_display = (
        'boucle_brebis',
        'date_gestation',
        'etat_gestation',
        'methode_confirmation',
        'mise_bas_estimee',  # méthode admin ci-dessous
    )
    list_filter = (
        'etat_gestation',
        'methode_confirmation',
        'date_gestation',
    )
    search_fields = (
        'boucle_brebis__boucle_ovin',   # FK vers Troupeau, champ 'boucle_ovin'
    )
    date_hierarchy = 'date_gestation'
    ordering = ('-date_gestation',)
    list_select_related = ('boucle_brebis',)
    autocomplete_fields = ('boucle_brebis',)

    # Formulaire
    fieldsets = (
        (None, {
            'fields': (
                'boucle_brebis',
                'date_gestation',
                'methode_confirmation',
                'etat_gestation',
                'observations',
                'mise_bas_estimee',   # lecture seule
            )
        }),
    )
    readonly_fields = ('mise_bas_estimee',)

    @admin.display(description="Mise-bas estimée", ordering='date_gestation')
    def mise_bas_estimee(self, obj):
        """
        Affiche la date estimée de mise-bas (propriété du modèle).
        Utilise un tiret cadratin si indisponible.
        """
        return obj.date_estimee_mise_bas or "—"

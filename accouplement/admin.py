from django.contrib import admin
from django.utils.html import format_html
from .models import Accouplement


@admin.register(Accouplement)
class AccouplementAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'boucle_brebis',
        'boucle_belier',
        'date_debut_lutte',
        'date_fin_lutte',
        'accouplement_reussi_icon',
    )
    list_filter = (
        'accouplement_reussi',
        'date_debut_lutte',
        'date_fin_lutte',
    )
    search_fields = (
        'boucle_belier__boucle_ovin',   # <- corrigé
        'boucle_brebis__boucle_ovin',   # <- corrigé
    )
    readonly_fields = ('accouplement_reussi',)
    autocomplete_fields = ('boucle_brebis', 'boucle_belier')
    list_select_related = ('boucle_brebis', 'boucle_belier')
    date_hierarchy = 'date_debut_lutte'
    ordering = ['-date_debut_lutte']

    fieldsets = (
        ("Informations générales", {
            'fields': ('boucle_brebis', 'boucle_belier', 'observations')
        }),
        ("Période de lutte", {
            'fields': ('date_debut_lutte', 'date_fin_lutte')
        }),
        ("Suivi de gestation", {
            'fields': ('date_verification_gestation', 'date_gestation', 'accouplement_reussi')
        }),
    )

    @admin.display(description='Réussi', ordering='accouplement_reussi')
    def accouplement_reussi_icon(self, obj):
        if obj.accouplement_reussi:
            return format_html('<span style="color:green; font-weight:bold;">✔</span>')
        return format_html('<span style="color:red; font-weight:bold;">✘</span>')

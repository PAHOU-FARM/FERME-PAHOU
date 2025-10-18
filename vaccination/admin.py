from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Vaccination


@admin.register(Vaccination)
class VaccinationAdmin(admin.ModelAdmin):
    list_display = (
        'boucle_ovin_display',
        'date_vaccination',
        'type_vaccin',
        'nom_vaccin',
        'dose_formatee',
        'voie_administration',
        'nom_veterinaire',
    )
    search_fields = (
        'boucle_ovin__boucle_ovin',
        'type_vaccin',
        'nom_vaccin',
        'nom_veterinaire',
    )
    list_filter = (
        'voie_administration',
        'type_vaccin',
        'date_vaccination',
    )
    ordering = ('-date_vaccination',)
    autocomplete_fields = ('boucle_ovin',)
    date_hierarchy = 'date_vaccination'
    list_select_related = ('boucle_ovin',)
    empty_value_display = '—'

    fieldsets = (
        (_('Informations vaccination'), {
            'fields': (
                'boucle_ovin',
                'date_vaccination',
            )
        }),
        (_('Détails vaccin'), {
            'fields': (
                'type_vaccin',
                'nom_vaccin',
                'dose_vaccin',
                'voie_administration',
            )
        }),
        (_('Responsable'), {
            'fields': (
                'nom_veterinaire',
                'observations',
            )
        }),
    )

    @admin.display(description=_("Boucle"))
    def boucle_ovin_display(self, obj):
        # Affiche le numéro de boucle (snake_case), sinon un tiret
        return getattr(obj.boucle_ovin, 'boucle_ovin', self.empty_value_display)

    @admin.display(description=_("Dose"))
    def dose_formatee(self, obj):
        try:
            return f"{float(obj.dose_vaccin):.2f} mL"
        except (TypeError, ValueError):
            return self.empty_value_display

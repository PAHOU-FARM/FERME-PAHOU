from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from .models import Reproduction


@admin.register(Reproduction)
class ReproductionAdmin(admin.ModelAdmin):
    list_display = (
        'femelle_boucle',
        'male_boucle',
        'date_accouplement',
        'has_gestation',
        'has_naissance',
        'date_creation',
    )
    list_filter = (
        'accouplement__date_debut_lutte',
        'date_creation',
    )
    search_fields = (
        'femelle__boucle_ovin',
        'male__boucle_ovin',
        'accouplement__boucle_brebis__boucle_ovin',
        'accouplement__boucle_belier__boucle_ovin',
    )
    readonly_fields = (
        'date_creation',
        'date_mise_a_jour',
        'accouplement_link',
        'gestation_link',
        'naissance_link',
    )
    # Champs affichés dans le formulaire d’édition
    fields = (
        'femelle',
        'male',
        'accouplement',
        'gestation',
        'naissance',
        'observations',
        'date_creation',
        'date_mise_a_jour',
        'accouplement_link',
        'gestation_link',
        'naissance_link',
    )
    ordering = ('-accouplement__date_debut_lutte',)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related('femelle', 'male', 'accouplement', 'gestation', 'naissance')
        )

    # ----- colonnes list_display -----
    def femelle_boucle(self, obj):
        return getattr(obj.femelle, 'boucle_ovin', '—')
    femelle_boucle.short_description = "Femelle"

    def male_boucle(self, obj):
        return getattr(obj.male, 'boucle_ovin', '—')
    male_boucle.short_description = "Mâle"

    def date_accouplement(self, obj):
        return getattr(obj.accouplement, 'date_debut_lutte', None)
    date_accouplement.short_description = "Début lutte"
    date_accouplement.admin_order_field = 'accouplement__date_debut_lutte'

    def has_gestation(self, obj):
        return bool(obj.gestation)
    has_gestation.boolean = True
    has_gestation.short_description = "Gestation ?"

    def has_naissance(self, obj):
        return bool(obj.naissance)
    has_naissance.boolean = True
    has_naissance.short_description = "Naissance ?"

    # ----- liens vers admin des objets liés (lecture seule) -----
    def accouplement_link(self, obj):
        if obj.accouplement_id:
            url = reverse('admin:accouplement_accouplement_change', args=[obj.accouplement_id])
            label = str(obj.accouplement)
            return format_html('<a href="{}">{}</a>', url, label)
        return '—'
    accouplement_link.short_description = "Accouplement (admin)"

    def gestation_link(self, obj):
        if obj.gestation_id:
            url = reverse('admin:gestation_gestation_change', args=[obj.gestation_id])
            label = str(obj.gestation)
            return format_html('<a href="{}">{}</a>', url, label)
        return '—'
    gestation_link.short_description = "Gestation (admin)"

    def naissance_link(self, obj):
        if obj.naissance_id:
            url = reverse('admin:naissance_naissance_change', args=[obj.naissance_id])
            label = str(obj.naissance)
            return format_html('<a href="{}">{}</a>', url, label)
        return '—'
    naissance_link.short_description = "Naissance (admin)"

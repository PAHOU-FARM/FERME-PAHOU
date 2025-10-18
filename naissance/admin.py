from django.contrib import admin
from .models import Naissance, Agneau


class AgneauInline(admin.TabularInline):
    model = Agneau
    extra = 1
    # On laisse éditable pour pouvoir choisir la boucle de l’agneau
    autocomplete_fields = ('boucle',)
    verbose_name = "Agneau"
    verbose_name_plural = "Agneaux"


@admin.register(Naissance)
class NaissanceAdmin(admin.ModelAdmin):
    list_display = (
        'date_mise_bas',
        'boucle_mere',
        'origine_accouplement',
        'get_pere',
        'accouplement',
    )
    list_filter = (
        'origine_accouplement',
        ('date_mise_bas', admin.DateFieldListFilter),
    )
    search_fields = (
        'boucle_mere__boucle_ovin',
        'nom_male_externe',
        'accouplement__boucle_belier__boucle_ovin',
    )
    date_hierarchy = 'date_mise_bas'
    ordering = ('-date_mise_bas',)

    readonly_fields = ('get_pere',)
    inlines = [AgneauInline]

    # Confort / perf
    autocomplete_fields = ('boucle_mere', 'accouplement')
    list_select_related = ('boucle_mere', 'accouplement', 'accouplement__boucle_belier')

    fieldsets = (
        (None, {
            'fields': (
                'boucle_mere',
                'date_mise_bas',
                'origine_accouplement',
                'accouplement',
                'nom_male_externe',
                'observations',
                'get_pere',
            )
        }),
    )

    @admin.display(description="Père")
    def get_pere(self, obj):
        # Utilise la propriété cohérente du modèle (pere_label)
        return obj.pere_label

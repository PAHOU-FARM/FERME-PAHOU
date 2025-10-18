from django.contrib import admin
from .models import Historiquetroupeau


@admin.register(Historiquetroupeau)
class HistoriquetroupeauAdmin(admin.ModelAdmin):
    """
    Admin lecture seule pour l’historique du troupeau.
    Si tu veux autoriser la suppression (purge), mets has_delete_permission() -> True.
    """

    # --- LISTE ---
    list_display = (
        'troupeau_display',
        'date_evenement',
        'statut',
        'ancienne_boucle',
        'nouvelle_boucle',
        'ancien_statut',
        'nouveau_statut',
        'observations',
    )
    list_filter = ('statut', 'date_evenement')
    search_fields = (
        'troupeau__boucle_ovin',   # snake_case correct
        'ancienne_boucle',
        'nouvelle_boucle',
        'ancien_statut',
        'nouveau_statut',
        'observations',
    )
    date_hierarchy = 'date_evenement'
    ordering = ('-date_evenement',)
    list_select_related = ('troupeau',)
    autocomplete_fields = ('troupeau',)
    empty_value_display = '—'
    list_per_page = 50

    # --- FORM / DÉTAIL ---
    # On verrouille tous les champs pour rendre l’historique non éditable
    readonly_fields = (
        'troupeau',
        'date_evenement',
        'statut',
        'ancienne_boucle',
        'ancienne_naissance_date',
        'ancienne_boucle_active',
        'ancien_proprietaire',
        'ancienne_origine',
        'ancien_statut',
        'ancien_sexe',
        'ancienne_race',
        'ancienne_achat_date',
        'ancienne_entree_date',
        'ancienne_date_sortie',
        'nouvelle_boucle',
        'nouvelle_naissance_date',
        'nouvelle_boucle_active',
        'nouveau_proprietaire',
        'nouvelle_origine',
        'nouveau_statut',
        'nouveau_sexe',
        'nouvelle_race',
        'nouvelle_achat_date',
        'nouvelle_entree_date',
        'nouvelle_date_sortie',
        'observations',
    )

    fieldsets = (
        ('Référence', {
            'fields': ('troupeau', 'date_evenement', 'statut', 'observations')
        }),
        ('Anciennes valeurs', {
            'classes': ('collapse',),
            'fields': (
                'ancienne_boucle',
                'ancienne_naissance_date',
                'ancienne_boucle_active',
                'ancien_proprietaire',
                'ancienne_origine',
                'ancien_statut',
                'ancien_sexe',
                'ancienne_race',
                'ancienne_achat_date',
                'ancienne_entree_date',
                'ancienne_date_sortie',
            )
        }),
        ('Nouvelles valeurs', {
            'classes': ('collapse',),
            'fields': (
                'nouvelle_boucle',
                'nouvelle_naissance_date',
                'nouvelle_boucle_active',
                'nouveau_proprietaire',
                'nouvelle_origine',
                'nouveau_statut',
                'nouveau_sexe',
                'nouvelle_race',
                'nouvelle_achat_date',
                'nouvelle_entree_date',
                'nouvelle_date_sortie',
            )
        }),
    )

    # --- Droits (lecture seule) ---
    def has_add_permission(self, request):
        # empêche la création manuelle d’entrées d’historique
        return False

    def has_change_permission(self, request, obj=None):
        # empêche la modification manuelle
        return False

    def has_delete_permission(self, request, obj=None):
        # Historique souvent conservé => False.
        # Mets True si tu veux autoriser la purge manuelle.
        return False

    # --- Optimisation ---
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('troupeau')

    # --- Affichage ---
    @admin.display(description="Boucle Ovin", ordering='troupeau__boucle_ovin')
    def troupeau_display(self, obj):
        # La FK peut être nulle (Suppression) → garde-fou
        return getattr(obj.troupeau, 'boucle_ovin', '—')

from django.contrib import admin
from .models import Croissance


@admin.register(Croissance)
class CroissanceAdmin(admin.ModelAdmin):
    # Affichage liste (poids/taille formatés)
    list_display = (
        'Boucle_Ovin',
        'Date_mesure',
        'poids_fmt',
        'taille_fmt',
        'Etat_Sante',
        'Croissance_Evaluation',
        'est_historique',
    )
    list_filter = ('Etat_Sante', 'Croissance_Evaluation', 'est_historique', 'Date_mesure')
    search_fields = (
        'Boucle_Ovin__boucle_ovin',   # champ réel du modèle Troupeau
        'Observations',
    )
    date_hierarchy = 'Date_mesure'
    ordering = ('-Date_mesure', '-id')
    list_per_page = 25

    # Formulaire
    readonly_fields = ('est_historique',)

    # Optimisations / confort
    list_select_related = ('Boucle_Ovin',)   # évite N+1 sur la FK
    autocomplete_fields = ('Boucle_Ovin',)   # fonctionne si TroupeauAdmin a bien search_fields sur 'boucle_ovin'

    def get_queryset(self, request):
        # Optimise et garde l’ordre souhaité
        return (
            super()
            .get_queryset(request)
            .select_related('Boucle_Ovin')
            .order_by('-Date_mesure', '-id')
        )

    # --- Colonnes formatées ---
    @admin.display(description="Poids (kg)", ordering='Poids_Kg')
    def poids_fmt(self, obj):
        return f"{obj.Poids_Kg:.2f}" if obj.Poids_Kg is not None else "—"

    @admin.display(description="Taille (cm)", ordering='Taille_CM')
    def taille_fmt(self, obj):
        return f"{obj.Taille_CM:.2f}" if obj.Taille_CM is not None else "—"


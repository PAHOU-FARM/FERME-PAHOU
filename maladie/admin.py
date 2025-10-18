from django.contrib import admin
from django.utils.html import format_html
from .models import Maladie


@admin.register(Maladie)
class MaladieAdmin(admin.ModelAdmin):
    # ----- Liste -----
    list_display = (
        'boucle_ovin_display',
        'Nom_Maladie',
        'Date_observation',
        'Statut_badge',
        'Gravite_badge',
        'Veterinaire',
        'cout_fcfa_format',
    )
    list_display_links = ('boucle_ovin_display', 'Nom_Maladie')
    list_filter = ('Nom_Maladie', 'Gravite', 'Statut', 'Date_observation')
    search_fields = (
        'Boucle_Ovin__boucle_ovin',  # <-- champ du modèle Troupeau
        'Nom_Maladie',
        'Veterinaire',
        'Symptomes_Observes',
        'Observations',
    )
    ordering = ('-Date_observation', '-id')
    date_hierarchy = 'Date_observation'
    list_per_page = 25

    # Optimisations
    list_select_related = ('Boucle_Ovin',)
    autocomplete_fields = ('Boucle_Ovin',)

    # ----- Formulaire -----
    fieldsets = (
        ('Identification de l’animal', {
            'fields': ('Boucle_Ovin',)
        }),
        ('Détails de la maladie', {
            'fields': (
                'Nom_Maladie',
                'Symptomes_Observes',
                'Date_observation',
                'Date_guerison',
                'Statut',
                'Gravite',
                'Observations',
            )
        }),
        ('Traitement', {
            'fields': (
                'Traitement_Administre',
                'Duree_Traitement',
                'Cout_Traitement_FCFA',
                'Veterinaire',
            )
        }),
    )

    # Optionnel : rendez la date d’observation non éditable après création
    # readonly_fields = ('Date_observation',)

    # ====== Affichages formatés ======
    @admin.display(description="Boucle", ordering='Boucle_Ovin__boucle_ovin')
    def boucle_ovin_display(self, obj: Maladie):
        # Affiche la boucle si dispo, sinon l’ID
        return getattr(obj.Boucle_Ovin, 'boucle_ovin', obj.Boucle_Ovin_id)

    @admin.display(description="Coût (FCFA)", ordering='Cout_Traitement_FCFA')
    def cout_fcfa_format(self, obj: Maladie):
        val = obj.Cout_Traitement_FCFA
        if val is None:
            return "—"
        # Format français simple: espace milliers + virgule décimale
        s = f"{val:,.2f}".replace(',', ' ').replace('.', ',')
        return f"{s} F CFA"

    @admin.display(description="Statut", ordering='Statut')
    def Statut_badge(self, obj: Maladie):
        # Petits badges Bootstrap-like
        mapping = {
            'Actif': 'primary',
            'Résolu': 'success',
            'Chronique': 'warning',
        }
        color = mapping.get(obj.Statut, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, obj.Statut)

    @admin.display(description="Gravité", ordering='Gravite')
    def Gravite_badge(self, obj: Maladie):
        mapping = {
            'Léger': 'success',
            'Modéré': 'warning',
            'Grave': 'danger',
            'Critique': 'dark',
        }
        color = mapping.get(obj.Gravite, 'secondary')
        label = obj.Gravite or '—'
        return format_html('<span class="badge bg-{}">{}</span>', color, label)

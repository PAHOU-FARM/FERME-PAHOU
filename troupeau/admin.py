from datetime import date
from django.contrib import admin
from django import forms
from django.forms import DateInput, NumberInput, Textarea
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import Troupeau


class TroupeauAdminForm(forms.ModelForm):
    class Meta:
        model = Troupeau
        fields = '__all__'
        widgets = {
            'naissance_date': DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'achat_date': DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'entree_date': DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'date_sortie': DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'poids_initial': NumberInput(attrs={'step': '0.1', 'min': '0', 'class': 'form-control'}),
            'taille_initiale': NumberInput(attrs={'step': '0.1', 'min': '0', 'class': 'form-control'}),
            'observations': Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'pere_boucle' in self.fields:
            self.fields['pere_boucle'].queryset = (
                Troupeau.objects.filter(sexe='male', boucle_active=True).order_by('boucle_ovin')
            )
            self.fields['pere_boucle'].empty_label = "Père inconnu"

        if 'mere_boucle' in self.fields:
            self.fields['mere_boucle'].queryset = (
                Troupeau.objects.filter(sexe='femelle', boucle_active=True).order_by('boucle_ovin')
            )
            self.fields['mere_boucle'].empty_label = "Mère inconnue"


@admin.register(Troupeau)
class TroupeauAdmin(admin.ModelAdmin):
    form = TroupeauAdminForm

    list_display = (
        'boucle_avec_couleur',
        'sexe_avec_icone',
        'race',
        'naissance_date',
        'get_age_ovin',
        'get_statut_avec_couleur',
        'origine_ovin',
        'proprietaire_ovin',
        'get_consanguinite',
        'get_reproducteur_status',
        'boucle_active',
    )
    list_display_links = ('boucle_avec_couleur',)

    list_filter = ('sexe', 'race', 'statut', 'origine_ovin', 'proprietaire_ovin', 'boucle_active')
    search_fields = ('boucle_ovin', 'pere_boucle__boucle_ovin', 'mere_boucle__boucle_ovin', 'observations')
    list_editable = ('boucle_active',)
    ordering = ('-naissance_date', 'boucle_ovin')
    list_per_page = 25
    raw_id_fields = ('pere_boucle', 'mere_boucle')
    readonly_fields = ('coefficient_consanguinite', 'get_age_en_details', 'get_descendants_count', 'children_links')

    fieldsets = (
        ('Identification', {
            'fields': ('boucle_ovin', 'sexe', 'race'),
            'classes': ('wide',)
        }),
        ('Dates importantes', {
            'fields': ('naissance_date', ('achat_date', 'entree_date'), 'date_sortie'),
            'classes': ('collapse',)
        }),
        ('Généalogie', {
            'fields': ('pere_boucle', 'mere_boucle', 'coefficient_consanguinite', 'children_links'),
            'classes': ('collapse',)
        }),
        ('Mesures physiques', {
            'fields': ('poids_initial', 'taille_initiale'),
            'classes': ('collapse',)
        }),
        ('Statut et origine', {
            'fields': ('statut', 'boucle_active', ('origine_ovin', 'proprietaire_ovin'))
        }),
        ('Notes', {
            'fields': ('observations',),
            'classes': ('collapse',)
        }),
    )

    # ----- Affichages -----
    @admin.display(description="Boucle", ordering='boucle_ovin')
    def boucle_avec_couleur(self, obj):
        couleur = '#28a745' if obj.boucle_active else '#dc3545'
        return format_html('<span style="color:{};font-weight:bold">{}</span>', couleur, obj.boucle_ovin)

    @admin.display(description="Sexe", ordering='sexe')
    def sexe_avec_icone(self, obj):
        label = obj.get_sexe_display()
        return format_html('♂️ {}', label) if obj.sexe == 'male' else format_html('♀️ {}', label)

    @admin.display(description="Âge", ordering='-naissance_date')
    def get_age_ovin(self, obj):
        age = obj.age_ovin
        if age is None:
            return format_html('<em style="color:#999">Inconnu</em>')
        if age < 1:
            return format_html('<span style="color:#17a2b8;font-weight:bold">moins d’1 an</span>')
        if age > 7:
            return format_html('<span style="color:#fd7e14;font-weight:bold">{} ans</span>', age)
        return format_html('<span style="color:#28a745;font-weight:bold">{} an{s}</span>', age, s='s' if age > 1 else '')

    @admin.display(description="Statut", ordering='statut')
    def get_statut_avec_couleur(self, obj):
        couleurs = {'naissance': '#17a2b8', 'achat': '#28a745', 'vendu': '#ffc107', 'decede': '#dc3545', 'sortie': '#6c757d'}
        return format_html('<span style="color:{};font-weight:bold">{}</span>', couleurs.get(obj.statut, '#333'), obj.get_statut_display())

    @admin.display(description="Consanguinité", ordering='coefficient_consanguinite')
    def get_consanguinite(self, obj):
        coeff = obj.coefficient_consanguinite or 0.0
        pct = coeff * 100
        if coeff == 0:
            return format_html('<span style="color:#28a745">0%</span>')
        if coeff < 0.0625:
            return format_html('<span style="color:#ffc107">{:.1f}%</span>', pct)
        return format_html('<span style="color:#dc3545;font-weight:bold">{:.1f}% ⚠️</span>', pct)

    @admin.display(description="Reproducteur", boolean=True)
    def get_reproducteur_status(self, obj):
        return bool(obj.naissance_date and obj.is_reproducteur_age)

    @admin.display(description="Âge détaillé")
    def get_age_en_details(self, obj):
        if not obj.naissance_date:
            return "Date de naissance non renseignée"
        today = date.today()
        years = today.year - obj.naissance_date.year
        months = today.month - obj.naissance_date.month
        if (today.day, today.month) < (obj.naissance_date.day, obj.naissance_date.month):
            months -= 1
        if months < 0:
            years -= 1
            months += 12
        parts = []
        if years > 0:
            parts.append(f"{years} an{'s' if years > 1 else ''}")
        if months > 0:
            parts.append(f"{months} mois")
        return " et ".join(parts) if parts else "moins d'1 mois"

    @admin.display(description="Descendants")
    def get_descendants_count(self, obj):
        count = obj.agneaux_pere.count() if obj.sexe == 'male' else obj.agneaux_mere.count()
        return f"{count} descendant{'s' if count > 1 else ''}"

    @admin.display(description="Enfants directs (lecture seule)")
    def children_links(self, obj):
        enfants = list(obj.get_descendants())
        if not enfants:
            return mark_safe('<span class="text-muted">Aucun enfant enregistré.</span>')
        links = []
        for e in enfants[:20]:
            url = f"/admin/troupeau/troupeau/{e.pk}/change/"
            links.append(f'<a href="{url}">{e.boucle_ovin}</a>')
        extra = '' if len(enfants) <= 20 else f' … (+{len(enfants)-20})'
        return mark_safe(", ".join(links) + extra)

    # ----- Actions -----
    @admin.action(description="Activer les boucles sélectionnées")
    def activer_boucles(self, request, queryset):
        updated = queryset.update(boucle_active=True)
        self.message_user(request, f"{updated} boucle(s) activée(s).")

    @admin.action(description="Désactiver les boucles sélectionnées")
    def desactiver_boucles(self, request, queryset):
        updated = queryset.update(boucle_active=False)
        self.message_user(request, f"{updated} boucle(s) désactivée(s).")

    @admin.action(description="Marquer comme vendus")
    def marquer_vendus(self, request, queryset):
        updated = queryset.update(statut='vendu', boucle_active=False, date_sortie=date.today())
        self.message_user(request, f"{updated} animal(aux) marqué(s) comme vendu(s).")

    @admin.action(description="Recalculer la consanguinité")
    def recalculer_consanguinite(self, request, queryset):
        count = 0
        for obj in queryset:
            nouveau = obj.coefficient_consanguinite_wright()
            if (obj.coefficient_consanguinite or 0.0) != nouveau:
                obj.coefficient_consanguinite = nouveau
                obj.save(update_fields=['coefficient_consanguinite'])
                count += 1
        self.message_user(request, f"Consanguinité recalculée pour {count} animal(aux).")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('pere_boucle', 'mere_boucle')

    class Media:
        css = {'all': ('admin/css/troupeau_admin.css',)}
        js = ('admin/js/troupeau_admin.js',)

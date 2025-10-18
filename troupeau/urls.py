# troupeau/urls.py
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from . import views

app_name = 'troupeau'

urlpatterns = [
    # === URLS DE BASE ===
    path('', RedirectView.as_view(pattern_name='troupeau:liste'), name='accueil'),
    path('liste/arbre/', views.TroupeauTreeView.as_view(), name='liste_arbre'),

    # Ancienne URL (compat)
    path('formulaire/', views.troupeau_formulaire, name='troupeau_formulaire'),

    # === GESTION CRUD COMPLÈTE ===
    path('liste/', views.TroupeauListView.as_view(), name='liste'),
    path('<int:pk>/', views.TroupeauDetailView.as_view(), name='detail'),
    path('nouveau/', views.TroupeauCreateView.as_view(), name='nouveau'),
    path('<int:pk>/modifier/', views.TroupeauUpdateView.as_view(), name='modifier'),
    path('<int:pk>/supprimer/', views.TroupeauDeleteView.as_view(), name='supprimer'),

    # === FONCTIONNALITÉS SPÉCIALISÉES ===
    path('<int:pk>/genealogie/', views.troupeau_genealogie, name='genealogie'),
    path('<int:pk>/descendants/', views.troupeau_descendants, name='descendants'),
    path('reproducteurs/', views.troupeau_reproducteurs, name='reproducteurs'),

    # ⚠️ Harmonisé avec tes templates : `rapport_consanguinite`
    path('rapport-consanguinite/', views.rapport_consanguinite, name='rapport_consanguinite'),

    # === ACTIONS ET OUTILS ===
    path('actions-masse/', views.troupeau_actions_masse, name='actions_masse'),
    path('recalculer-consanguinite/', views.recalculer_consanguinite, name='recalculer_consanguinite'),
    path('valider-donnees/', views.valider_donnees_troupeau, name='valider_donnees'),

    # === RAPPORTS ET STATISTIQUES ===
    path('dashboard/', views.troupeau_dashboard, name='dashboard'),
    path('rapports/', views.troupeau_rapports, name='rapports'),
    path('rapports/ages/', views.rapport_ages, name='rapport_ages'),
    path('rapports/races/', views.rapport_races, name='rapport_races'),
    path('rapports/reproducteurs/', views.rapport_reproducteurs, name='rapport_reproducteurs'),

    # === EXPORT ET IMPORT ===
    path('export/csv/', views.export_troupeau_csv, name='export_csv'),
    path('export/excel/', views.export_troupeau_excel, name='export_excel'),
    path('export/pdf/', views.export_troupeau_pdf, name='export_pdf'),
    path('import/', views.import_troupeau, name='import'),

    # ⚠️ Harmonisé : nom = download_import_template (utilisé par tes vues/menus)
    path('download-template/', views.download_import_template, name='download_import_template'),

    # === API ET AJAX ===
    path('api/recherche/', views.api_recherche_animaux, name='api_recherche'),
    path('api/parents-disponibles/', views.api_parents_disponibles, name='api_parents_disponibles'),
    path('api/genealogie/<int:pk>/', views.api_genealogie, name='api_genealogie'),
    path('api/valider-boucle/', views.api_valider_boucle, name='api_valider_boucle'),
    path('api/calculer-consanguinite/', views.api_calculer_consanguinite, name='api_calculer_consanguinite'),

    # === UTILITAIRES ===
    path('etiquettes/', views.generer_etiquettes, name='etiquettes'),
    path('<int:pk>/etiquette/', views.generer_etiquette_individuelle, name='etiquette_individuelle'),
    path('<int:pk>/historique/', views.troupeau_historique, name='historique'),

    # === FILTRES AVANCÉS ===
    path('actifs/', views.TroupeauListView.as_view(extra_context={'filter': 'actifs'}), name='actifs'),
    path('inactifs/', views.TroupeauListView.as_view(extra_context={'filter': 'inactifs'}), name='inactifs'),
    path('males/', views.TroupeauListView.as_view(extra_context={'filter': 'males'}), name='males'),
    path('femelles/', views.TroupeauListView.as_view(extra_context={'filter': 'femelles'}), name='femelles'),
    path('jeunes/', views.troupeau_jeunes, name='jeunes'),
    path('ages/', views.troupeau_ages, name='ages'),
    path('race/<str:race>/', views.troupeau_par_race, name='par_race'),
    path('proprietaire/<str:proprietaire>/', views.troupeau_par_proprietaire, name='par_proprietaire'),

    # === MAINTENANCE ET ADMIN (placeholder -> redirige vers liste) ===
    path('maintenance/', include([
        path('', RedirectView.as_view(pattern_name='troupeau:liste'), name='maintenance'),
        path('nettoyer-historique/', RedirectView.as_view(pattern_name='troupeau:liste'), name='nettoyer_historique'),
        path('verifier-coherence/', RedirectView.as_view(pattern_name='troupeau:liste'), name='verifier_coherence'),
        path('sauvegarder/', RedirectView.as_view(pattern_name='troupeau:liste'), name='sauvegarder'),
        path('restaurer/', RedirectView.as_view(pattern_name='troupeau:liste'), name='restaurer'),
    ])),

    # === URLS SPÉCIALISÉES PAR CONTEXTE (placeholders) ===
    path('elevage/', include([
        path('', RedirectView.as_view(pattern_name='troupeau:liste'), name='dashboard_elevage'),
        path('saillies/', RedirectView.as_view(pattern_name='troupeau:liste'), name='planning_saillies'),
        path('gestations/', RedirectView.as_view(pattern_name='troupeau:liste'), name='suivi_gestations'),
        path('naissances/', RedirectView.as_view(pattern_name='troupeau:liste'), name='registre_naissances'),
    ])),
    path('commercial/', include([
        path('', RedirectView.as_view(pattern_name='troupeau:liste'), name='dashboard_commercial'),
        path('disponibles/', RedirectView.as_view(pattern_name='troupeau:liste'), name='disponibles_vente'),
        path('vendus/', RedirectView.as_view(pattern_name='troupeau:liste'), name='vendus'),
        path('prix/', RedirectView.as_view(pattern_name='troupeau:liste'), name='gestion_prix'),
    ])),
    path('sanitaire/', include([
        path('', RedirectView.as_view(pattern_name='troupeau:liste'), name='dashboard_sanitaire'),
        path('vaccinations/', RedirectView.as_view(pattern_name='troupeau:liste'), name='planning_vaccinations'),
        path('traitements/', RedirectView.as_view(pattern_name='troupeau:liste'), name='historique_traitements'),
        path('quarantaine/', RedirectView.as_view(pattern_name='troupeau:liste'), name='quarantaine'),
    ])),
]

# === PATTERNS DE DÉVELOPPEMENT ===
if settings.DEBUG:
    urlpatterns += [
        path('dev/', include([
            path('test-formulaire/', RedirectView.as_view(pattern_name='troupeau:troupeau_formulaire'), name='test_formulaire'),
            path('test-validation/', RedirectView.as_view(pattern_name='troupeau:liste'), name='test_validation'),
            path('demo-donnees/', RedirectView.as_view(pattern_name='troupeau:liste'), name='demo_donnees'),
        ])),
    ]

# historiquetroupeau/urls.py
from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "historiquetroupeau"

urlpatterns = [
    # Liste complète de l’historique
    path("", views.HistoriquetroupeauListView.as_view(), name="liste"),

    # Détail d’une entrée d’historique
    path("<int:pk>/", views.HistoriquetroupeauDetailView.as_view(), name="detail"),

    # Historique pour un animal donné
    # -> ex: /historiques/troupeau/123/historique/
    path(
        "troupeau/<int:pk>/historique/",
        views.HistoriqueParTroupeauListView.as_view(),
        name="par_troupeau",
    ),

    # Route de compatibilité (anciens liens)
    path(
        "par-troupeau/<int:pk>/",
        RedirectView.as_view(
            pattern_name="historiquetroupeau:par_troupeau",
            permanent=True,
        ),
        name="par_troupeau_legacy",
    ),

    # Dashboard (si le template existe)
    path("dashboard/", views.tableau_de_bord, name="dashboard"),

    # Export CSV
    path("export/csv/", views.export_historique_csv, name="export_csv"),

    # API JSON
    path("api/", views.api_historique_list, name="api_list"),
    path("api/stats/", views.api_historique_stats, name="api_stats"),
]

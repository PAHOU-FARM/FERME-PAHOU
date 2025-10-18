# accouplement/urls.py
from django.urls import path
from . import views

app_name = "accouplement"

urlpatterns = [
    # Liste / dashboard / détail
    path("", views.AccouplementListView.as_view(), name="liste"),
    path("dashboard/", views.dashboard, name="dashboard"),  # <- lien "Dashboard" de la sidebar
    path("<int:pk>/", views.AccouplementDetailView.as_view(), name="detail"),

    # Création / édition / suppression
    path("nouveau/", views.AccouplementCreateView.as_view(), name="nouveau"),
    path("<int:pk>/modifier/", views.AccouplementUpdateView.as_view(), name="modifier"),
    path("<int:pk>/supprimer/", views.AccouplementDeleteView.as_view(), name="supprimer"),

    # Utilitaires
    path("export/csv/", views.export_accouplements_csv, name="export_csv"),
    path("api/", views.api_accouplements, name="api_list"),
]

# croissance/urls.py
from django.urls import path
from .views import (
    CroissanceListView,
    CroissanceDetailView,
    CroissanceCreateView,
    CroissanceUpdateView,
    CroissanceDeleteView,
    CroissanceDashboardView,   # ✅ importer la vue dashboard
)

app_name = "croissance"

urlpatterns = [
    path("", CroissanceListView.as_view(), name="croissance_list"),
    path("detail/<int:pk>/", CroissanceDetailView.as_view(), name="croissance_detail"),
    path("ajouter/", CroissanceCreateView.as_view(), name="croissance_create"),
    path("modifier/<int:pk>/", CroissanceUpdateView.as_view(), name="croissance_update"),
    path("supprimer/<int:pk>/", CroissanceDeleteView.as_view(), name="croissance_delete"),
    path("dashboard/", CroissanceDashboardView.as_view(), name="croissance_dashboard"),  # ✅
]

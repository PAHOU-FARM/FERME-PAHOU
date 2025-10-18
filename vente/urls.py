from django.urls import path
from .views import (
    VenteListView,
    VenteDetailView,
    VenteCreateView,
    VenteUpdateView,
    VenteDeleteView,
    dashboard,
)

app_name = "vente"

urlpatterns = [
    path("", VenteListView.as_view(), name="vente_list"),
    path("ajouter/", VenteCreateView.as_view(), name="vente_create"),
    path("<int:pk>/", VenteDetailView.as_view(), name="vente_detail"),
    path("modifier/<int:pk>/", VenteUpdateView.as_view(), name="vente_update"),
    path("supprimer/<int:pk>/", VenteDeleteView.as_view(), name="vente_delete"),
    path("dashboard/", dashboard, name="dashboard"),
]

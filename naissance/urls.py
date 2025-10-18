# naissance/urls.py
from django.urls import path
from .views import (
    NaissanceListView,
    NaissanceDetailView,
    NaissanceCreateView,
    NaissanceUpdateView,
    NaissanceDeleteView,
    NaissanceDashboardView,
)

app_name = "naissance"

urlpatterns = [
    path("", NaissanceListView.as_view(), name="naissance_list"),
    path("ajouter/", NaissanceCreateView.as_view(), name="naissance_create"),
    path("<int:pk>/", NaissanceDetailView.as_view(), name="naissance_detail"),
    path("modifier/<int:pk>/", NaissanceUpdateView.as_view(), name="naissance_update"),
    path("supprimer/<int:pk>/", NaissanceDeleteView.as_view(), name="naissance_delete"),
    path("dashboard/", NaissanceDashboardView.as_view(), name="naissance_dashboard"),
]

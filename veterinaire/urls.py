# veterinaire/urls.py
from django.urls import path
from .views import (
    VeterinaireListView,
    VeterinaireDetailView,
    VeterinaireCreateView,
    VeterinaireUpdateView,
    VeterinaireDeleteView,
    veterinaire_dashboard,   # <-- important
)

app_name = "veterinaire"

urlpatterns = [
    path("", VeterinaireListView.as_view(), name="veterinaire_list"),
    path("dashboard/", veterinaire_dashboard, name="veterinaire_dashboard"),
    path("ajouter/", VeterinaireCreateView.as_view(), name="veterinaire_create"),
    path("<int:pk>/", VeterinaireDetailView.as_view(), name="veterinaire_detail"),
    path("modifier/<int:pk>/", VeterinaireUpdateView.as_view(), name="veterinaire_update"),
    path("supprimer/<int:pk>/", VeterinaireDeleteView.as_view(), name="veterinaire_delete"),
]

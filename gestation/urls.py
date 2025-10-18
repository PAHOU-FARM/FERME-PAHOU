# gestation/urls.py
from django.urls import path
from . import views  # on référence tout via "views."

app_name = "gestation"

urlpatterns = [
    path("", views.GestationListView.as_view(), name="gestation_list"),
    path("ajouter/", views.GestationCreateView.as_view(), name="gestation_create"),
    path("<int:pk>/", views.GestationDetailView.as_view(), name="gestation_detail"),
    path("modifier/<int:pk>/", views.GestationUpdateView.as_view(), name="gestation_update"),
    path("supprimer/<int:pk>/", views.GestationDeleteView.as_view(), name="gestation_delete"),

    # Dashboard (2 alias pour couvrir les templates existants)
    path("dashboard/", views.dashboard, name="gestation_dashboard"),
    path("tableau-de-bord/", views.dashboard, name="dashboard"),
]

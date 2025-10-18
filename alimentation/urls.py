from django.urls import path
from . import views  # import du module pour éviter les erreurs d'attribut

app_name = "alimentation"

urlpatterns = [
    path("", views.AlimentationListView.as_view(), name="alimentation_list"),
    path("ajouter/", views.AlimentationCreateView.as_view(), name="alimentation_create"),
    path("modifier/<int:pk>/", views.AlimentationUpdateView.as_view(), name="alimentation_update"),
    path("supprimer/<int:pk>/", views.AlimentationDeleteView.as_view(), name="alimentation_delete"),

    # (Optionnel) si tu ajoutes un tableau de bord plus tard :
     path("dashboard/", views.dashboard, name="alimentation_dashboard"),

    # (Optionnel) si tu crées une vue détail :
    # path("<int:pk>/", views.AlimentationDetailView.as_view(), name="alimentation_detail"),
]

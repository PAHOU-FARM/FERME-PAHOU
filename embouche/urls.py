from django.urls import path
from .views import (
    EmboucheListView,
    EmboucheDetailView,
    EmboucheCreateView,
    EmboucheUpdateView,
    EmboucheDeleteView,
    dashboard,
)

app_name = "embouche"

urlpatterns = [
    path("", EmboucheListView.as_view(), name="embouche_list"),
    path("ajouter/", EmboucheCreateView.as_view(), name="embouche_create"),
    path("<int:pk>/", EmboucheDetailView.as_view(), name="embouche_detail"),
    path("modifier/<int:pk>/", EmboucheUpdateView.as_view(), name="embouche_update"),
    path("supprimer/<int:pk>/", EmboucheDeleteView.as_view(), name="embouche_delete"),
    path("dashboard/", dashboard, name="dashboard"),
]

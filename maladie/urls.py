# maladie/urls.py
from django.urls import path
from . import views

app_name = "maladie"

urlpatterns = [
    path("", views.MaladieListView.as_view(), name="maladie_list"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("ajouter/", views.MaladieCreateView.as_view(), name="maladie_create"),
    path("<int:pk>/", views.MaladieDetailView.as_view(), name="maladie_detail"),
    path("modifier/<int:pk>/", views.MaladieUpdateView.as_view(), name="maladie_update"),
    path("supprimer/<int:pk>/", views.MaladieDeleteView.as_view(), name="maladie_delete"),
]

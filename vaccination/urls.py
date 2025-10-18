# vaccination/urls.py
from django.urls import path
from . import views

app_name = "vaccination"

urlpatterns = [
    path("", views.VaccinationListView.as_view(), name="vaccination_list"),
    path("dashboard/", views.vaccination_dashboard, name="vaccination_dashboard"),
    path("ajouter/", views.VaccinationCreateView.as_view(), name="vaccination_create"),
    path("<int:pk>/", views.VaccinationDetailView.as_view(), name="vaccination_detail"),
    path("modifier/<int:pk>/", views.VaccinationUpdateView.as_view(), name="vaccination_update"),
    path("supprimer/<int:pk>/", views.VaccinationDeleteView.as_view(), name="vaccination_delete"),
]

# reproduction/urls.py
from django.urls import path
from . import views

app_name = "reproduction"

urlpatterns = [
    # Liste
    path("", views.ReproductionListView.as_view(), name="reproduction_list"),

    # CRUD
    path("ajouter/", views.ReproductionCreateView.as_view(), name="reproduction_create"),
    path("<int:pk>/", views.ReproductionDetailView.as_view(), name="reproduction_detail"),
    path("modifier/<int:pk>/", views.ReproductionUpdateView.as_view(), name="reproduction_update"),
    path("supprimer/<int:pk>/", views.ReproductionDeleteView.as_view(), name="reproduction_delete"),

    # Dashboard (nom utilisé par la sidebar : reproduction:reproduction_dashboard)
    path("dashboard/", views.dashboard, name="reproduction_dashboard"),
]

from django.urls import path
from . import views

app_name = "genealogie"

urlpatterns = [
    path("", views.GenealogieListView.as_view(), name="liste"),
    path("<int:pk>/", views.GenealogieDetailView.as_view(), name="detail"),
    path("nouveau/", views.GenealogieCreateView.as_view(), name="nouveau"),
    path("modifier/<int:pk>/", views.GenealogieUpdateView.as_view(), name="modifier"),
    path("supprimer/<int:pk>/", views.GenealogieDeleteView.as_view(), name="supprimer"),
]

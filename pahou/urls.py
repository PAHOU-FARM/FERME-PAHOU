# pahou/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView, RedirectView
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path("admin/", admin.site.urls),

    # 🔁 Redirection de la racine vers /accueil/
    path("", RedirectView.as_view(pattern_name="accueil", permanent=False)),

    # Auth / comptes
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),

    # Accueil (protégé : login requis)
    path(
        "accueil/",
        login_required(
            TemplateView.as_view(template_name="accueil.html"),
            login_url="/accounts/login/",  # ✅ garde cette redirection explicite
        ),
        name="accueil",
    ),

    # Apps métier
    path("troupeau/", include(("troupeau.urls", "troupeau"), namespace="troupeau")),
    path("historique/", include(("historiquetroupeau.urls", "historiquetroupeau"), namespace="historiquetroupeau")),
    path("accouplement/", include(("accouplement.urls", "accouplement"), namespace="accouplement")),
    path("alimentation/", include(("alimentation.urls", "alimentation"), namespace="alimentation")),
    path("croissance/", include(("croissance.urls", "croissance"), namespace="croissance")),
    path("embouche/", include(("embouche.urls", "embouche"), namespace="embouche")),
    path("genealogie/", include(("genealogie.urls", "genealogie"), namespace="genealogie")),
    path("gestation/", include(("gestation.urls", "gestation"), namespace="gestation")),
    path("maladie/", include(("maladie.urls", "maladie"), namespace="maladie")),
    path("naissance/", include(("naissance.urls", "naissance"), namespace="naissance")),
    path("reproduction/", include(("reproduction.urls", "reproduction"), namespace="reproduction")),
    path("vaccination/", include(("vaccination.urls", "vaccination"), namespace="vaccination")),
    path("veterinaire/", include(("veterinaire.urls", "veterinaire"), namespace="veterinaire")),
    path("vente/", include(("vente.urls", "vente"), namespace="vente")),
]

# Fichiers statiques & médias en développement
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

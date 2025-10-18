# historiquetroupeau/views.py
from datetime import datetime, timedelta
import csv

from django.db.models import Q, Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.generic import ListView, DetailView

from .models import Historiquetroupeau
from troupeau.models import Troupeau


# ========= Helpers =========

def _parse_date(val):
    """
    Accepte 'YYYY-MM-DD' ou 'DD/MM/YYYY' -> date | None (pas d'exception).
    """
    if not val:
        return None
    s = str(val).strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _filtered_queryset(request):
    """
    Filtres communs (liste, export, API):
      - q : texte (boucle, statut, observations, anciennes/nouvelles boucles)
      - statut : égalité exacte
      - from / to : bornes inclusives sur date_evenement (date)
      - troupeau_id : par animal (id)
    """
    qs = Historiquetroupeau.objects.select_related("troupeau")

    q = (request.GET.get("q") or "").strip()
    statut = (request.GET.get("statut") or "").strip()
    dfrom = _parse_date(request.GET.get("from"))
    dto = _parse_date(request.GET.get("to"))
    troupeau_id = (request.GET.get("troupeau_id") or "").strip()

    if q:
        qs = qs.filter(
            Q(troupeau__boucle_ovin__icontains=q) |
            Q(statut__icontains=q) |
            Q(ancienne_boucle__icontains=q) |
            Q(nouvelle_boucle__icontains=q) |
            Q(observations__icontains=q)
        )

    if statut:
        qs = qs.filter(statut=statut)

    if dfrom:
        qs = qs.filter(date_evenement__gte=dfrom)
    if dto:
        qs = qs.filter(date_evenement__lte=dto)

    if troupeau_id.isdigit():
        qs = qs.filter(troupeau_id=int(troupeau_id))

    return qs.order_by("-date_evenement", "-id")


# ========= Vues HTML =========

class HistoriquetroupeauListView(ListView):
    """
    Liste filtrable/paginée de l'historique.
    GET: q, statut, from, to, troupeau_id
    """
    model = Historiquetroupeau
    template_name = "historiquetroupeau/liste.html"
    context_object_name = "evenements"
    paginate_by = 25

    def get_queryset(self):
        return _filtered_queryset(self.request)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        base_qs = _filtered_queryset(self.request)
        ctx["total"] = base_qs.count()
        ctx["par_statut"] = (
            base_qs.values("statut")
                  .annotate(c=Count("id"))
                  .order_by("-c")
        )
        ctx["filters"] = {
            "q": self.request.GET.get("q", ""),
            "statut": self.request.GET.get("statut", ""),
            "from": self.request.GET.get("from", ""),
            "to": self.request.GET.get("to", ""),
            "troupeau_id": self.request.GET.get("troupeau_id", ""),
        }
        return ctx


class HistoriquetroupeauDetailView(DetailView):
    """Détail d’un événement d’historique."""
    model = Historiquetroupeau
    template_name = "historiquetroupeau/detail.html"
    context_object_name = "evt"


class HistoriqueParTroupeauListView(ListView):
    """
    Historique pour un animal donné.
    URL: path('par-troupeau/<int:pk>/', HistoriqueParTroupeauListView.as_view(), name='par_troupeau')
    Template attendu : templates/historiquetroupeau/par_troupeau.html
    """
    model = Historiquetroupeau
    template_name = "historiquetroupeau/par_troupeau.html"  # <-- aligne avec le template fourni
    context_object_name = "evenements"
    paginate_by = 25

    def get_queryset(self):
        self.animal = get_object_or_404(Troupeau, pk=self.kwargs["pk"])
        return (
            Historiquetroupeau.objects
            .filter(troupeau=self.animal)
            .order_by("-date_evenement", "-id")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["animal"] = self.animal
        return ctx


# ========= Export CSV =========

def export_historique_csv(request):
    """
    Export CSV des événements filtrés (mêmes filtres que la liste).
    """
    qs = _filtered_queryset(request)

    # UTF-8 + BOM pour Excel
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="historique_{timezone.localdate().isoformat()}.csv"'
    response.write("\ufeff")

    writer = csv.writer(response, delimiter=";", lineterminator="\n")
    writer.writerow([
        "Date", "Boucle", "Statut",
        "Ancienne boucle", "Nouvelle boucle",
        "Ancien statut", "Nouveau statut",
        "Observations",
    ])

    for evt in qs:
        boucle = evt.troupeau.boucle_ovin if evt.troupeau else ""
        writer.writerow([
            evt.date_evenement.strftime("%d/%m/%Y") if evt.date_evenement else "",
            boucle,
            evt.statut or "",
            evt.ancienne_boucle or "",
            evt.nouvelle_boucle or "",
            evt.ancien_statut or "",
            evt.nouveau_statut or "",
            (evt.observations or "").replace("\n", " ").strip(),
        ])

    return response


# ========= API JSON =========

def api_historique_list(request):
    """
    GET /historiquetroupeau/api/?q=&statut=&from=&to=&troupeau_id=
    Retourne les événements filtrés (max 500) au format JSON.
    """
    qs = _filtered_queryset(request)[:500]
    data = [{
        "id": e.id,
        "date_evenement": e.date_evenement.isoformat() if e.date_evenement else None,
        "statut": e.statut,
        "troupeau_id": e.troupeau_id,
        "boucle": e.troupeau.boucle_ovin if e.troupeau else None,
        "ancienne_boucle": e.ancienne_boucle,
        "nouvelle_boucle": e.nouvelle_boucle,
        "ancien_statut": e.ancien_statut,
        "nouveau_statut": e.nouveau_statut,
        "observations": e.observations,
    } for e in qs]
    return JsonResponse({"results": data})


def api_historique_stats(request):
    """
    GET /historiquetroupeau/api/stats/?days=30
    Retourne des stats rapides : total, par statut, et série récente (J-<days> → J).
    """
    try:
        days = int(request.GET.get("days", 30))
    except ValueError:
        days = 30
    days = max(1, min(days, 365))

    today = timezone.localdate()
    since = today - timedelta(days=days)

    qs = Historiquetroupeau.objects.all()
    total = qs.count()
    par_statut = list(qs.values("statut").annotate(c=Count("id")).order_by("-c"))

    recent_qs = (
        qs.filter(date_evenement__gte=since)
          .values("date_evenement")
          .annotate(c=Count("id"))
          .order_by("date_evenement")
    )
    recent = [{"date": r["date_evenement"].isoformat(), "count": r["c"]} for r in recent_qs]

    return JsonResponse({
        "total": total,
        "par_statut": par_statut,
        "recent": recent,
        "since": since.isoformat(),
        "until": today.isoformat(),
        "window_days": days,
    })


# ========= Petit dashboard HTML =========

def tableau_de_bord(request):
    """
    Tableau de bord simple pour l'historique (exposé si tu as un template 'historiquetroupeau/dashboard.html').
    """
    total = Historiquetroupeau.objects.count()
    par_statut = (
        Historiquetroupeau.objects
        .values("statut").annotate(c=Count("id"))
        .order_by("-c")
    )
    derniers = (
        Historiquetroupeau.objects
        .select_related("troupeau")
        .order_by("-date_evenement", "-id")[:20]
    )
    return render(request, "historiquetroupeau/dashboard.html", {
        "total": total,
        "par_statut": par_statut,
        "derniers": derniers,
    })

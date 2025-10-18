# accouplement/views.py
from datetime import datetime

import csv
from django.contrib import messages
from django.db.models import Q, Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .models import Accouplement
from troupeau.models import Troupeau


# ======================
# Helpers
# ======================

def _parse_date(val):
    """Accepte 'YYYY-MM-DD' ou 'DD/MM/YYYY' -> date | None."""
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
    Filtre commun utilisé par List + Export + API.
    GET pris en charge:
      - q : texte sur boucle brebis/bélier
      - reussi : 0/1 (false/true)
      - from, to : dates (sur date_debut_lutte)
      - brebis_id, belier_id : IDs de Troupeau
    """
    qs = Accouplement.objects.select_related("boucle_brebis", "boucle_belier").all()

    q = (request.GET.get("q") or "").strip()
    reussi = (request.GET.get("reussi") or "").strip()
    dfrom = _parse_date(request.GET.get("from"))
    dto = _parse_date(request.GET.get("to"))
    brebis_id = (request.GET.get("brebis_id") or "").strip()
    belier_id = (request.GET.get("belier_id") or "").strip()

    if q:
        qs = qs.filter(
            Q(boucle_brebis__boucle_ovin__icontains=q)
            | Q(boucle_belier__boucle_ovin__icontains=q)
        )

    if reussi.lower() in {"1", "true", "yes", "oui"}:
        qs = qs.filter(accouplement_reussi=True)
    elif reussi.lower() in {"0", "false", "no", "non"}:
        qs = qs.filter(accouplement_reussi=False)

    if dfrom:
        qs = qs.filter(date_debut_lutte__gte=dfrom)
    if dto:
        qs = qs.filter(date_debut_lutte__lte=dto)

    if brebis_id.isdigit():
        qs = qs.filter(boucle_brebis_id=int(brebis_id))
    if belier_id.isdigit():
        qs = qs.filter(boucle_belier_id=int(belier_id))

    return qs.order_by("-date_debut_lutte", "-id")


# ======================
# Vues HTML
# ======================

class AccouplementListView(ListView):
    model = Accouplement
    template_name = "accouplement/liste.html"
    context_object_name = "accouplements"
    paginate_by = 25

    def get_queryset(self):
        return _filtered_queryset(self.request)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        base = _filtered_queryset(self.request)
        ctx["total"] = base.count()
        ctx["reussis"] = base.filter(accouplement_reussi=True).count()
        ctx["en_cours"] = base.filter(accouplement_reussi=False).count()
        ctx["par_mois"] = (
            base.values("date_debut_lutte__year", "date_debut_lutte__month")
            .annotate(c=Count("id"))
            .order_by("-date_debut_lutte__year", "-date_debut_lutte__month")
        )
        # valeurs de filtres pour le formulaire
        ctx["filters"] = {
            "q": self.request.GET.get("q", ""),
            "reussi": self.request.GET.get("reussi", ""),
            "from": self.request.GET.get("from", ""),
            "to": self.request.GET.get("to", ""),
            "brebis_id": self.request.GET.get("brebis_id", ""),
            "belier_id": self.request.GET.get("belier_id", ""),
        }
        return ctx


class AccouplementDetailView(DetailView):
    model = Accouplement
    template_name = "accouplement/detail.html"
    context_object_name = "acc"


class _FormQuerysetMixin:
    """Ajuste les querysets des selects pour ne proposer que les animaux actifs du bon sexe."""
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Proposer uniquement les animaux actifs du bon sexe
        if "boucle_brebis" in form.fields:
            form.fields["boucle_brebis"].queryset = (
                Troupeau.objects.filter(sexe="femelle", boucle_active=True).order_by("boucle_ovin")
            )
        if "boucle_belier" in form.fields:
            form.fields["boucle_belier"].queryset = (
                Troupeau.objects.filter(sexe="male", boucle_active=True).order_by("boucle_ovin")
            )
        return form


class AccouplementCreateView(_FormQuerysetMixin, CreateView):
    model = Accouplement
    template_name = "accouplement/form.html"
    fields = [
        "boucle_brebis", "boucle_belier",
        "date_debut_lutte", "date_fin_lutte",
        "date_verification_gestation", "date_gestation",
        "observations",
    ]
    success_url = reverse_lazy("accouplement:liste")

    def form_valid(self, form):
        messages.success(self.request, "Accouplement créé avec succès.")
        return super().form_valid(form)


class AccouplementUpdateView(_FormQuerysetMixin, UpdateView):
    model = Accouplement
    template_name = "accouplement/form.html"
    fields = [
        "boucle_brebis", "boucle_belier",
        "date_debut_lutte", "date_fin_lutte",
        "date_verification_gestation", "date_gestation",
        "observations",
    ]
    success_url = reverse_lazy("accouplement:liste")
    context_object_name = "acc"

    def form_valid(self, form):
        messages.success(self.request, "Accouplement mis à jour avec succès.")
        return super().form_valid(form)


class AccouplementDeleteView(DeleteView):
    model = Accouplement
    template_name = "accouplement/confirm_suppression.html"
    success_url = reverse_lazy("accouplement:liste")
    context_object_name = "acc"

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Accouplement supprimé avec succès.")
        return super().delete(request, *args, **kwargs)


# ======================
# Dashboard (nouveau)
# ======================

def dashboard(request):
    """
    Tableau de bord : tuiles synthèse + répartition par mois + derniers enregistrements.
    """
    total = Accouplement.objects.count()
    reussis = Accouplement.objects.filter(accouplement_reussi=True).count()
    non_reussis = Accouplement.objects.filter(accouplement_reussi=False).count()

    par_mois = (
        Accouplement.objects
        .values("date_debut_lutte__year", "date_debut_lutte__month")
        .annotate(c=Count("id"))
        .order_by("-date_debut_lutte__year", "-date_debut_lutte__month")
    )

    recents = (
        Accouplement.objects
        .select_related("boucle_brebis", "boucle_belier")
        .order_by("-date_debut_lutte", "-id")[:10]
    )

    ctx = {
        "total": total,
        "reussis": reussis,
        "non_reussis": non_reussis,
        "par_mois": list(par_mois),
        "recents": list(recents),
    }
    return render(request, "accouplement/dashboard.html", ctx)


# ======================
# Export CSV
# ======================

def export_accouplements_csv(request):
    qs = _filtered_queryset(request)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="accouplements.csv"'
    writer = csv.writer(response, delimiter=";")

    writer.writerow([
        "Brebis", "Bélier",
        "Début lutte", "Fin lutte",
        "Vérif gestation", "Date gestation",
        "Réussi", "Observations",
    ])

    for a in qs:
        writer.writerow([
            getattr(a.boucle_brebis, "boucle_ovin", ""),
            getattr(a.boucle_belier, "boucle_ovin", ""),
            a.date_debut_lutte.isoformat() if a.date_debut_lutte else "",
            a.date_fin_lutte.isoformat() if a.date_fin_lutte else "",
            a.date_verification_gestation.isoformat() if a.date_verification_gestation else "",
            a.date_gestation.isoformat() if a.date_gestation else "",
            "Oui" if a.accouplement_reussi else "Non",
            (a.observations or "").replace("\n", " ").strip(),
        ])

    return response


# ======================
# API JSON simple
# ======================

def api_accouplements(request):
    """
    GET /accouplement/api/?q=&reussi=&from=&to=&brebis_id=&belier_id=
    -> results: [{...}] (max 500)
    """
    qs = _filtered_queryset(request)[:500]
    data = []
    for a in qs:
        data.append({
            "id": a.id,
            "brebis_id": a.boucle_brebis_id,
            "brebis_boucle": getattr(a.boucle_brebis, "boucle_ovin", None),
            "belier_id": a.boucle_belier_id,
            "belier_boucle": getattr(a.boucle_belier, "boucle_ovin", None),
            "date_debut_lutte": a.date_debut_lutte.isoformat() if a.date_debut_lutte else None,
            "date_fin_lutte": a.date_fin_lutte.isoformat() if a.date_fin_lutte else None,
            "date_verification_gestation": a.date_verification_gestation.isoformat() if a.date_verification_gestation else None,
            "date_gestation": a.date_gestation.isoformat() if a.date_gestation else None,
            "accouplement_reussi": a.accouplement_reussi,
            "observations": a.observations,
        })
    return JsonResponse({"results": data})

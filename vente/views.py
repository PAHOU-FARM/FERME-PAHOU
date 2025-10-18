from datetime import datetime
from decimal import Decimal

from django.contrib import messages
from django.db.models import Q, Sum, Avg, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import ListView, DetailView

from .models import Vente
from .forms import VenteForm


# ---------- Helpers ----------
def _parse_date(val):
    """Accepte 'YYYY-MM-DD' ou 'DD/MM/YYYY' et renvoie date() ou None."""
    if not val:
        return None
    s = str(val).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def _filtered_queryset(request):
    """
    Filtres:
      - q : texte (boucle, type_acheteur, propriétaire, observations)
      - acheteur : type_acheteur exact
      - proprio  : proprietaire_ovin exact
      - from/to  : bornes de date_vente
    """
    qs = Vente.objects.select_related("boucle_ovin").all()

    q = (request.GET.get("q") or "").strip()
    acheteur = (request.GET.get("acheteur") or "").strip()
    proprio = (request.GET.get("proprio") or "").strip()
    dfrom = _parse_date(request.GET.get("from"))
    dto = _parse_date(request.GET.get("to"))

    if q:
        qs = qs.filter(
            Q(boucle_ovin__boucle_ovin__icontains=q)
            | Q(type_acheteur__icontains=q)
            | Q(proprietaire_ovin__icontains=q)
            | Q(observations__icontains=q)
        )

    if acheteur:
        qs = qs.filter(type_acheteur=acheteur)
    if proprio:
        qs = qs.filter(proprietaire_ovin=proprio)
    if dfrom:
        qs = qs.filter(date_vente__gte=dfrom)
    if dto:
        qs = qs.filter(date_vente__lte=dto)

    return qs.order_by("-date_vente", "-id")


# ---------- List / Detail ----------
class VenteListView(ListView):
    model = Vente
    template_name = "vente/liste.html"
    context_object_name = "ventes"
    paginate_by = 25

    def get_queryset(self):
        return _filtered_queryset(self.request)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        base = _filtered_queryset(self.request)

        # Filtres pour le template
        ctx["filters"] = {
            "q": self.request.GET.get("q", ""),
            "acheteur": self.request.GET.get("acheteur", ""),
            "proprio": self.request.GET.get("proprio", ""),
            "from": self.request.GET.get("from", ""),
            "to": self.request.GET.get("to", ""),
        }

        # Stats rapides (protégées contre None)
        ctx["total"] = base.count()
        agg = base.aggregate(
            total_prix=Sum("prix_vente"),
            poids_moyen=Avg("poids_kg"),
        )
        ctx["total_prix"] = agg["total_prix"] or Decimal("0.00")
        ctx["poids_moyen"] = agg["poids_moyen"] or Decimal("0.00")

        # Répartitions
        ctx["par_type"] = list(base.values("type_acheteur").annotate(c=Count("id")).order_by("-c"))
        ctx["par_proprio"] = list(base.values("proprietaire_ovin").annotate(c=Count("id")).order_by("-c"))
        return ctx


class VenteDetailView(DetailView):
    model = Vente
    template_name = "vente/detail.html"
    context_object_name = "vente"


# ---------- Create / Update ----------
class VenteCreateView(View):
    def get(self, request):
        form = VenteForm()
        return render(request, "vente/form.html", {"form": form})

    def post(self, request):
        form = VenteForm(request.POST)
        if form.is_valid():
            try:
                obj = form.save()
                messages.success(request, "Vente enregistrée avec succès.")
                return redirect("vente:vente_detail", pk=obj.pk)
            except Exception as exc:
                messages.error(request, f"Erreur lors de l’enregistrement : {exc}")
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    messages.error(request, f"{field}: {err}")
        return render(request, "vente/form.html", {"form": form})


class VenteUpdateView(View):
    def get(self, request, pk):
        vente = get_object_or_404(Vente, pk=pk)
        form = VenteForm(instance=vente)
        return render(request, "vente/form.html", {"form": form, "vente": vente})

    def post(self, request, pk):
        vente = get_object_or_404(Vente, pk=pk)
        form = VenteForm(request.POST, instance=vente)
        if form.is_valid():
            try:
                obj = form.save()
                messages.success(request, "Vente mise à jour.")
                return redirect("vente:vente_detail", pk=obj.pk)
            except Exception as exc:
                messages.error(request, f"Erreur lors de la mise à jour : {exc}")
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    messages.error(request, f"{field}: {err}")
        return render(request, "vente/form.html", {"form": form, "vente": vente})


# ---------- Delete (avec confirmation) ----------
class VenteDeleteView(View):
    def get(self, request, pk):
        vente = get_object_or_404(Vente, pk=pk)
        return render(request, "vente/confirm_suppression.html", {"vente": vente})

    def post(self, request, pk):
        vente = get_object_or_404(Vente, pk=pk)
        try:
            vente.delete()
            messages.success(request, "Vente supprimée.")
        except Exception as exc:
            messages.error(request, f"Suppression impossible : {exc}")
        return redirect("vente:vente_list")


# ---------- Dashboard simple ----------
def dashboard(request):
    """
    Dashboard simple : totaux, répartitions et agrégations par mois sur le jeu filtré.
    """
    base = _filtered_queryset(request)
    agg = base.aggregate(
        total_prix=Sum("prix_vente"),
        poids_moyen=Avg("poids_kg"),
    )
    par_mois = (
        base.values("date_vente__year", "date_vente__month")
        .annotate(total=Sum("prix_vente"), n=Count("id"))
        .order_by("date_vente__year", "date_vente__month")
    )

    context = {
        "total": base.count(),
        "total_prix": agg["total_prix"] or Decimal("0.00"),
        "poids_moyen": agg["poids_moyen"] or Decimal("0.00"),
        "par_type": list(base.values("type_acheteur").annotate(c=Count("id")).order_by("-c")),
        "par_proprio": list(base.values("proprietaire_ovin").annotate(c=Count("id")).order_by("-c")),
        "par_mois": par_mois,
        "filters": {
            "q": request.GET.get("q", ""),
            "acheteur": request.GET.get("acheteur", ""),
            "proprio": request.GET.get("proprio", ""),
            "from": request.GET.get("from", ""),
            "to": request.GET.get("to", ""),
        },
    }
    return render(request, "vente/dashboard.html", context)

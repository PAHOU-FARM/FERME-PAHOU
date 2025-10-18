from datetime import datetime
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q, Count
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import ListView, DetailView, View

from .models import Reproduction
from .forms import ReproductionForm


def _parse_date(s):
    if not s:
        return None
    s = str(s).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


class ReproductionListView(ListView):
    model = Reproduction
    template_name = "reproduction/liste.html"
    context_object_name = "cycles"
    paginate_by = 25

    def get_queryset(self):
        qs = (
            Reproduction.objects.select_related(
                "femelle", "male", "accouplement", "gestation", "naissance"
            )
            .order_by("-accouplement__date_debut_lutte", "-date_creation")
        )

        q = (self.request.GET.get("q") or "").strip()
        dfrom = _parse_date(self.request.GET.get("from"))
        dto = _parse_date(self.request.GET.get("to"))
        has_gest = self.request.GET.get("gestation", "")
        has_nai = self.request.GET.get("naissance", "")

        if q:
            qs = qs.filter(
                Q(femelle__boucle_ovin__icontains=q)
                | Q(male__boucle_ovin__icontains=q)
                | Q(observations__icontains=q)
            )
        if dfrom:
            qs = qs.filter(accouplement__date_debut_lutte__gte=dfrom)
        if dto:
            qs = qs.filter(accouplement__date_debut_lutte__lte=dto)
        if has_gest in ("0", "1"):
            qs = qs.filter(gestation__isnull=(has_gest == "0"))
        if has_nai in ("0", "1"):
            qs = qs.filter(naissance__isnull=(has_nai == "0"))

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        base = self.get_queryset()
        ctx["total"] = base.count()
        ctx["avec_gestation"] = base.filter(gestation__isnull=False).count()
        ctx["avec_naissance"] = base.filter(naissance__isnull=False).count()
        ctx["filters"] = {
            "q": self.request.GET.get("q", ""),
            "from": self.request.GET.get("from", ""),
            "to": self.request.GET.get("to", ""),
            "gestation": self.request.GET.get("gestation", ""),
            "naissance": self.request.GET.get("naissance", ""),
        }
        return ctx


class ReproductionDetailView(DetailView):
    model = Reproduction
    template_name = "reproduction/detail.html"
    context_object_name = "cycle"


class ReproductionCreateView(View):
    def get(self, request):
        form = ReproductionForm()
        return render(request, "reproduction/form.html", {"form": form})

    def post(self, request):
        form = ReproductionForm(request.POST)
        if form.is_valid():
            try:
                cycle = form.save()
                messages.success(request, "Cycle de reproduction créé.")
                return redirect("reproduction:reproduction_detail", pk=cycle.pk)
            except (ValidationError, IntegrityError) as e:
                messages.error(request, f"Erreur : {getattr(e, 'message', str(e))}")
        else:
            for f, errs in form.errors.items():
                for err in errs:
                    messages.error(request, f"{f}: {err}")
        return render(request, "reproduction/form.html", {"form": form})


class ReproductionUpdateView(View):
    def get(self, request, pk):
        cycle = get_object_or_404(Reproduction, pk=pk)
        form = ReproductionForm(instance=cycle)
        return render(request, "reproduction/form.html", {"form": form, "cycle": cycle})

    def post(self, request, pk):
        cycle = get_object_or_404(Reproduction, pk=pk)
        form = ReproductionForm(request.POST, instance=cycle)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Cycle de reproduction mis à jour.")
                return redirect("reproduction:reproduction_detail", pk=pk)
            except (ValidationError, IntegrityError) as e:
                messages.error(request, f"Erreur : {getattr(e, 'message', str(e))}")
        else:
            for f, errs in form.errors.items():
                for err in errs:
                    messages.error(request, f"{f}: {err}")
        return render(request, "reproduction/form.html", {"form": form, "cycle": cycle})


class ReproductionDeleteView(View):
    def get(self, request, pk):
        cycle = get_object_or_404(Reproduction, pk=pk)
        return render(request, "reproduction/confirm_suppression.html", {"cycle": cycle})

    def post(self, request, pk):
        cycle = get_object_or_404(Reproduction, pk=pk)
        cycle.delete()
        messages.success(request, "Cycle de reproduction supprimé.")
        return redirect("reproduction:reproduction_list")


def dashboard(request):
    """
    Petit tableau de bord récapitulatif.
    """
    base = Reproduction.objects.select_related("femelle", "male", "accouplement")
    total = base.count()
    avec_gestation = base.filter(gestation__isnull=False).count()
    avec_naissance = base.filter(naissance__isnull=False).count()

    # Top femelles (par nombre de cycles)
    top_femelles = (
        base.values("femelle__boucle_ovin")
        .annotate(c=Count("id"))
        .order_by("-c")[:10]
    )
    # Top mâles (par nombre de cycles)
    top_males = (
        base.values("male__boucle_ovin")
        .annotate(c=Count("id"))
        .order_by("-c")[:10]
    )

    derniers = base.order_by("-accouplement__date_debut_lutte", "-date_creation")[:20]

    return render(
        request,
        "reproduction/dashboard.html",
        {
            "total": total,
            "avec_gestation": avec_gestation,
            "avec_naissance": avec_naissance,
            "top_femelles": top_femelles,
            "top_males": top_males,
            "derniers": derniers,
        },
    )

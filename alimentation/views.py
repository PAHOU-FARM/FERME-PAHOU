# alimentation/views.py
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.shortcuts import render

from .models import Alimentation
from .forms import AlimentationForm


class AlimentationListView(ListView):
    """
    Liste des alimentations.
    - Trie correct sur les champs CamelCase du modèle.
    - Recherche simple sur boucle, type, objectif et observations.
    """
    model = Alimentation
    template_name = "alimentation/liste.html"
    context_object_name = "alimentations"
    paginate_by = 25

    def get_queryset(self):
        qs = (
            Alimentation.objects
            .select_related("Boucle_Ovin")          # FK vers Troupeau
            .order_by("-Date_alimentation", "-id")
        )
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                Q(Boucle_Ovin__boucle_ovin__icontains=q) |
                Q(Observations__icontains=q) |
                Q(Type_Aliment__icontains=q) |
                Q(Objectif__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = (self.request.GET.get("q") or "").strip()
        return ctx


class AlimentationCreateView(CreateView):
    model = Alimentation
    form_class = AlimentationForm
    template_name = "alimentation/form.html"
    success_url = reverse_lazy("alimentation:alimentation_list")

    def form_valid(self, form):
        messages.success(self.request, "Alimentation ajoutée avec succès.")
        return super().form_valid(form)


class AlimentationUpdateView(UpdateView):
    model = Alimentation
    form_class = AlimentationForm
    template_name = "alimentation/form.html"
    success_url = reverse_lazy("alimentation:alimentation_list")

    def form_valid(self, form):
        messages.success(self.request, "Alimentation mise à jour avec succès.")
        return super().form_valid(form)


class AlimentationDeleteView(DeleteView):
    model = Alimentation
    template_name = "alimentation/confirm_delete.html"
    context_object_name = "alimentation"
    success_url = reverse_lazy("alimentation:alimentation_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Alimentation supprimée avec succès.")
        return super().delete(request, *args, **kwargs)


# --------------------------
# Dashboard
# --------------------------
def dashboard(request):
    """
    Tableau de bord Alimentation.
    Fournit le contexte attendu par templates/alimentation/dashboard.html :
      - stats: { total, total_kg, aujourdhui, mois_kg }
      - par_type: [{ type_aliment, type_aliment_label, count, total_kg }, ...]
      - par_objectif: [{ objectif, objectif_label, count }, ...]
      - recents: queryset des 10 derniers enregistrements (avec alias en minuscules)
    """
    # Date du jour (timezone-safe)
    today = getattr(timezone, "localdate", lambda: timezone.now().date())()

    # Cartes synthèse
    total = Alimentation.objects.count()
    total_kg = Alimentation.objects.aggregate(s=Sum("Quantite_Kg"))["s"]
    aujourdhui = Alimentation.objects.filter(Date_alimentation=today).count()
    mois_kg = (
        Alimentation.objects.filter(
            Date_alimentation__year=today.year,
            Date_alimentation__month=today.month,
        ).aggregate(s=Sum("Quantite_Kg"))["s"]
    )

    stats = {
        "total": total or 0,
        "total_kg": total_kg,
        "aujourdhui": aujourdhui or 0,
        "mois_kg": mois_kg,
    }

    # Libellés des choices
    type_choices = dict(Alimentation._meta.get_field("Type_Aliment").choices or [])
    obj_choices = dict(Alimentation._meta.get_field("Objectif").choices or [])

    # Répartition par type d’aliment
    _par_type = (
        Alimentation.objects
        .values("Type_Aliment")
        .annotate(count=Count("id"), total_kg=Sum("Quantite_Kg"))
        .order_by("Type_Aliment")
    )
    par_type = []
    for row in _par_type:
        val = row.get("Type_Aliment")
        par_type.append({
            "type_aliment": val,
            "type_aliment_label": type_choices.get(val, val),
            "count": row.get("count") or 0,
            "total_kg": row.get("total_kg"),
        })

    # Répartition par objectif
    _par_objectif = (
        Alimentation.objects
        .values("Objectif")
        .annotate(count=Count("id"))
        .order_by("Objectif")
    )
    par_objectif = []
    for row in _par_objectif:
        val = row.get("Objectif")
        par_objectif.append({
            "objectif": val,
            "objectif_label": obj_choices.get(val, val),
            "count": row.get("count") or 0,
        })

    # Derniers enregistrements
    recents = list(
        Alimentation.objects
        .select_related("Boucle_Ovin")
        .order_by("-Date_alimentation", "-id")[:10]
    )

    # ALIAS pour compatibilité avec le template (minuscules)
    # (le modèle est en CamelCase ; le template dashboard utilise des minuscules)
    for a in recents:
        a.boucle_ovin = a.Boucle_Ovin
        a.date_alimentation = a.Date_alimentation
        a.quantite_kg = a.Quantite_Kg
        # alias des méthodes get_FOO_display()
        a.get_type_aliment_display = (lambda _a=a: _a.get_Type_Aliment_display())
        a.get_objectif_display = (lambda _a=a: _a.get_Objectif_display())

    ctx = {
        "stats": stats,
        "par_type": par_type,
        "par_objectif": par_objectif,
        "recents": recents,
    }
    return render(request, "alimentation/dashboard.html", ctx)

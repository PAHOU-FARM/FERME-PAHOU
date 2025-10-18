# veterinaire/views.py
from datetime import datetime, timedelta

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Q, Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from .models import Veterinaire
from .forms import VeterinaireForm


# -----------------------------
# Helpers
# -----------------------------
def _parse_date(val):
    """Parse une date reçue en GET (YYYY-MM-DD ou DD/MM/YYYY)."""
    if not val:
        return None
    s = str(val).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _filtered_queryset(request):
    """
    Filtres GET gérés :
      - q : texte (boucle, véto, motif, traitement, obs, recommandations)
      - motif : égal (valeur exacte)
      - traitement : égal (valeur exacte)
      - from, to : bornes de date_visite (date)
      - troupeau_id : identifiant d'animal
    """
    qs = (
        Veterinaire.objects
        .select_related("troupeau", "maladie", "vaccination")
        .all()
    )

    q = (request.GET.get("q") or "").strip()
    motif = (request.GET.get("motif") or "").strip()
    traitement = (request.GET.get("traitement") or "").strip()
    dfrom = _parse_date(request.GET.get("from"))
    dto = _parse_date(request.GET.get("to"))
    troupeau_id = (request.GET.get("troupeau_id") or "").strip()

    if q:
        qs = qs.filter(
            Q(troupeau__boucle_ovin__icontains=q)
            | Q(nom_veterinaire__icontains=q)
            | Q(motif_de_la_visite__icontains=q)
            | Q(traitement_effectue__icontains=q)
            | Q(observations__icontains=q)
            | Q(recommandations__icontains=q)
        )

    if motif:
        qs = qs.filter(motif_de_la_visite=motif)

    if traitement:
        qs = qs.filter(traitement_effectue=traitement)

    if dfrom:
        qs = qs.filter(date_visite__gte=dfrom)
    if dto:
        qs = qs.filter(date_visite__lte=dto)

    if troupeau_id.isdigit():
        qs = qs.filter(troupeau_id=int(troupeau_id))

    return qs.order_by("-date_visite", "-id")


# -----------------------------
# Vues CRUD
# -----------------------------
class VeterinaireListView(View):
    paginate_by = 25  # prêt pour une pagination ultérieure si besoin

    def get(self, request):
        qs = _filtered_queryset(request)
        context = {
            "visites": qs,
            "filters": {
                "q": request.GET.get("q", ""),
                "motif": request.GET.get("motif", ""),
                "traitement": request.GET.get("traitement", ""),
                "from": request.GET.get("from", ""),
                "to": request.GET.get("to", ""),
                "troupeau_id": request.GET.get("troupeau_id", ""),
            },
        }
        return render(request, "veterinaire/liste.html", context)


class VeterinaireDetailView(View):
    def get(self, request, pk):
        obj = get_object_or_404(
            Veterinaire.objects.select_related("troupeau", "maladie", "vaccination"),
            pk=pk
        )
        return render(request, "veterinaire/detail.html", {"obj": obj})


class VeterinaireCreateView(View):
    def get(self, request):
        form = VeterinaireForm()
        return render(request, "veterinaire/form.html", {"form": form})

    def post(self, request):
        form = VeterinaireForm(request.POST)
        if form.is_valid():
            try:
                obj = form.save()
                messages.success(request, "Visite vétérinaire enregistrée.")
                return redirect("veterinaire:veterinaire_list")
            except ValidationError as e:
                if hasattr(e, "message_dict"):
                    for field, msgs in e.message_dict.items():
                        for m in (msgs if isinstance(msgs, (list, tuple)) else [msgs]):
                            messages.error(request, f"{field}: {m}")
                else:
                    messages.error(request, str(e))
            except IntegrityError:
                messages.error(
                    request,
                    "Conflit d’unicité : cette visite semble déjà enregistrée pour cet animal et cette date."
                )
            except Exception as e:
                messages.error(request, f"Erreur : {e}")
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    messages.error(request, f"{field}: {err}")
        return render(request, "veterinaire/form.html", {"form": form})


class VeterinaireUpdateView(View):
    def get(self, request, pk):
        obj = get_object_or_404(Veterinaire, pk=pk)
        form = VeterinaireForm(instance=obj)
        return render(request, "veterinaire/form.html", {"form": form, "obj": obj})

    def post(self, request, pk):
        obj = get_object_or_404(Veterinaire, pk=pk)
        form = VeterinaireForm(request.POST, instance=obj)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Visite vétérinaire mise à jour.")
                return redirect("veterinaire:veterinaire_list")
            except ValidationError as e:
                if hasattr(e, "message_dict"):
                    for field, msgs in e.message_dict.items():
                        for m in (msgs if isinstance(msgs, (list, tuple)) else [msgs]):
                            messages.error(request, f"{field}: {m}")
                else:
                    messages.error(request, str(e))
            except IntegrityError:
                messages.error(
                    request,
                    "Conflit d’unicité : cette visite semble déjà enregistrée pour cet animal et cette date."
                )
            except Exception as e:
                messages.error(request, f"Erreur : {e}")
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    messages.error(request, f"{field}: {err}")
        return render(request, "veterinaire/form.html", {"form": form, "obj": obj})


class VeterinaireDeleteView(View):
    def get(self, request, pk):
        obj = get_object_or_404(Veterinaire, pk=pk)
        return render(request, "veterinaire/confirm_suppression.html", {"obj": obj})

    def post(self, request, pk):
        obj = get_object_or_404(Veterinaire, pk=pk)
        try:
            obj.delete()
            messages.success(request, "Visite vétérinaire supprimée.")
        except Exception as e:
            messages.error(request, f"Suppression impossible : {e}")
        return redirect("veterinaire:veterinaire_list")


# -----------------------------
# Dashboard
# -----------------------------
def veterinaire_dashboard(request):
    """
    Tableau de bord vétérinaire : compte total, coût cumulé,
    nombre de visites sur 30 jours, répartition par motif, derniers enregistrements.
    """
    qs = (Veterinaire.objects
          .select_related("troupeau")
          .order_by("-date_visite", "-id"))

    total_visites = qs.count()
    cout_total = qs.aggregate(total=Sum("cout_visite"))["total"] or 0

    il_y_a_30j = timezone.localdate() - timedelta(days=30)
    derniers_30j = qs.filter(date_visite__gte=il_y_a_30j).count()

    par_motif = list(
        qs.values("motif_de_la_visite")
          .annotate(c=Count("id"))
          .order_by("-c")
    )

    context = {
        "total_visites": total_visites,
        "cout_total": cout_total,
        "derniers_30j": derniers_30j,
        "par_motif": par_motif,
        "derniers": qs[:20],
    }
    return render(request, "veterinaire/dashboard.html", context)

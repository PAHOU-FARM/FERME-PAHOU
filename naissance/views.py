# naissance/views.py
from datetime import datetime

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Q, Count, Avg
from django.shortcuts import get_object_or_404, render, redirect
from django.views import View

from .models import Naissance
from .forms import NaissanceForm


# --------- Helpers ---------
def _parse_date(val):
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
    Filtres supportés en GET :
      - q : texte (boucle mère, nom mâle externe, observations, boucles accouplement)
      - origine : Interne / Externe / Inconnu
      - from : date mini (date_mise_bas)
      - to   : date maxi (date_mise_bas)
    """
    qs = (
        Naissance.objects
        .select_related(
            "boucle_mere",
            "accouplement",
            "accouplement__boucle_brebis",
            "accouplement__boucle_belier",
        )
        .prefetch_related("agneaux")  # pour n.agneaux.count dans la liste
        .order_by("-date_mise_bas", "-id")
    )

    q = (request.GET.get("q") or "").strip()
    origine = (request.GET.get("origine") or "").strip()
    dfrom = _parse_date(request.GET.get("from"))
    dto = _parse_date(request.GET.get("to"))

    if q:
        qs = qs.filter(
            Q(boucle_mere__boucle_ovin__icontains=q) |
            Q(nom_male_externe__icontains=q) |
            Q(observations__icontains=q) |
            Q(accouplement__boucle_brebis__boucle_ovin__icontains=q) |
            Q(accouplement__boucle_belier__boucle_ovin__icontains=q)
        )

    if origine in ("Interne", "Externe", "Inconnu"):
        qs = qs.filter(origine_accouplement=origine)

    if dfrom:
        qs = qs.filter(date_mise_bas__gte=dfrom)
    if dto:
        qs = qs.filter(date_mise_bas__lte=dto)

    return qs


# --------- Vues ---------

class NaissanceListView(View):
    """Liste paginée avec filtres."""
    PAGE_SIZE = 25

    def get(self, request):
        qs = _filtered_queryset(request)
        paginator = Paginator(qs, self.PAGE_SIZE)
        page_obj = paginator.get_page(request.GET.get("page"))

        ctx = {
            "naissances": page_obj,             # itérable dans le template
            "page_obj": page_obj,               # pour la pagination
            "is_paginated": page_obj.has_other_pages(),
            "filters": {
                "q": request.GET.get("q", ""),
                "origine": request.GET.get("origine", ""),
                "from": request.GET.get("from", ""),
                "to": request.GET.get("to", ""),
            },
        }
        return render(request, "naissance/liste.html", ctx)


class NaissanceDetailView(View):
    def get(self, request, pk):
        naissance = get_object_or_404(
            Naissance.objects.select_related(
                "boucle_mere",
                "accouplement",
                "accouplement__boucle_brebis",
                "accouplement__boucle_belier",
            ).prefetch_related("agneaux__boucle"),
            pk=pk,
        )
        return render(request, "naissance/detail.html", {"naissance": naissance})


class NaissanceCreateView(View):
    def get(self, request):
        form = NaissanceForm()
        return render(request, "naissance/form.html", {"form": form})

    def post(self, request):
        form = NaissanceForm(request.POST)
        if form.is_valid():
            try:
                obj = form.save()
                messages.success(request, "Naissance enregistrée avec succès.")
                return redirect("naissance:naissance_detail", pk=obj.pk)
            except ValidationError as e:
                if hasattr(e, "message_dict"):
                    for field, msgs in e.message_dict.items():
                        for m in (msgs if isinstance(msgs, (list, tuple)) else [msgs]):
                            messages.error(request, f"{field}: {m}")
                else:
                    messages.error(request, str(e))
            except IntegrityError:
                messages.error(request, "Doublon : une naissance existe déjà pour cette mère à cette date.")
            except Exception as e:
                messages.error(request, f"Erreur : {e}")
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    messages.error(request, f"{field}: {err}")

        return render(request, "naissance/form.html", {"form": form})


class NaissanceUpdateView(View):
    def get(self, request, pk):
        naissance = get_object_or_404(Naissance, pk=pk)
        form = NaissanceForm(instance=naissance)
        return render(request, "naissance/form.html", {"form": form, "naissance": naissance})

    def post(self, request, pk):
        naissance = get_object_or_404(Naissance, pk=pk)
        form = NaissanceForm(request.POST, instance=naissance)
        if form.is_valid():
            try:
                obj = form.save()
                messages.success(request, "Naissance mise à jour.")
                return redirect("naissance:naissance_detail", pk=obj.pk)
            except ValidationError as e:
                if hasattr(e, "message_dict"):
                    for field, msgs in e.message_dict.items():
                        for m in (msgs if isinstance(msgs, (list, tuple)) else [msgs]):
                            messages.error(request, f"{field}: {m}")
                else:
                    messages.error(request, str(e))
            except IntegrityError:
                messages.error(request, "Doublon : une naissance existe déjà pour cette mère à cette date.")
            except Exception as e:
                messages.error(request, f"Erreur : {e}")
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    messages.error(request, f"{field}: {err}")

        return render(request, "naissance/form.html", {"form": form, "naissance": naissance})


class NaissanceDeleteView(View):
    # Page de confirmation
    def get(self, request, pk):
        naissance = get_object_or_404(Naissance, pk=pk)
        return render(request, "naissance/confirm_suppression.html", {"naissance": naissance})

    # Suppression
    def post(self, request, pk):
        naissance = get_object_or_404(Naissance, pk=pk)
        try:
            naissance.delete()
            messages.success(request, "Naissance supprimée.")
        except Exception as e:
            messages.error(request, f"Suppression impossible : {e}")
            return redirect("naissance:naissance_detail", pk=pk)
        return redirect("naissance:naissance_list")


# --------- Dashboard ---------

class NaissanceDashboardView(View):
    """
    Petit tableau de bord simple :
      - total
      - répartition par origine (Interne/Externe/Inconnu)
      - taille moyenne de portée (nb d’agneaux / naissance)
      - derniers enregistrements
    """
    def get(self, request):
        base = Naissance.objects.all()

        total = base.count()
        repartition = (
            base.values("origine_accouplement")
                .annotate(c=Count("id"))
                .order_by("-c")
        )

        # moyenne #agneaux / naissance
        avg_portee = (
            base.annotate(n=Count("agneaux"))
                .aggregate(v=Avg("n"))
                .get("v")
        )

        recents = (
            base.select_related("boucle_mere")
                .order_by("-date_mise_bas", "-id")[:20]
        )

        ctx = {
            "total": total,
            "repartition": repartition,
            "avg_portee": avg_portee,
            "recents": recents,
        }
        return render(request, "naissance/dashboard.html", ctx)

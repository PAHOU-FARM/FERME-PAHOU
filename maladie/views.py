# maladie/views.py
from datetime import datetime
import csv  # (si besoin plus tard pour export)

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import IntegrityError
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from .forms import MaladieForm
from .models import Maladie


# ========= Helpers =========

def _parse_date(val):
    """
    Accepte 'YYYY-MM-DD' ou 'DD/MM/YYYY' -> date | None (sans lever d'exception).
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


def _filtered_qs(request):
    """
    Filtres GET supportés :
      - q         : texte (boucle, nom maladie, symptômes, véto, observations)
      - statut    : égalité exacte
      - gravite   : égalité exacte
      - from, to  : bornes inclusives sur Date_observation (date)
    """
    qs = Maladie.objects.select_related("Boucle_Ovin")

    q = (request.GET.get("q") or "").strip()
    statut = (request.GET.get("statut") or "").strip()
    gravite = (request.GET.get("gravite") or "").strip()
    dfrom = _parse_date(request.GET.get("from"))
    dto = _parse_date(request.GET.get("to"))

    if q:
        qs = qs.filter(
            Q(Boucle_Ovin__boucle_ovin__icontains=q) |
            Q(Nom_Maladie__icontains=q) |
            Q(Symptomes_Observes__icontains=q) |
            Q(Veterinaire__icontains=q) |
            Q(Observations__icontains=q)
        )

    if statut:
        qs = qs.filter(Statut=statut)

    if gravite:
        qs = qs.filter(Gravite=gravite)

    if dfrom:
        qs = qs.filter(Date_observation__gte=dfrom)
    if dto:
        qs = qs.filter(Date_observation__lte=dto)

    return qs.order_by("-Date_observation", "-id")


# ========= Vues HTML =========

class MaladieListView(View):
    paginate_by = 25

    def get(self, request):
        base_qs = _filtered_qs(request)

        paginator = Paginator(base_qs, self.paginate_by)
        page = request.GET.get("page")

        try:
            page_obj = paginator.get_page(page)
        except PageNotAnInteger:
            page_obj = paginator.get_page(1)
        except EmptyPage:
            page_obj = paginator.get_page(paginator.num_pages)

        ctx = {
            "maladies": page_obj.object_list,
            "page_obj": page_obj,
            "is_paginated": page_obj.has_other_pages(),
            "filters": {
                "q": request.GET.get("q", ""),
                "statut": request.GET.get("statut", ""),
                "gravite": request.GET.get("gravite", ""),
                "from": request.GET.get("from", ""),
                "to": request.GET.get("to", ""),
            },
        }
        return render(request, "maladie/liste.html", ctx)


class MaladieDetailView(View):
    def get(self, request, pk):
        maladie = get_object_or_404(Maladie, pk=pk)
        return render(request, "maladie/detail.html", {"maladie": maladie})


class MaladieCreateView(View):
    def get(self, request):
        form = MaladieForm()
        return render(request, "maladie/form.html", {"form": form})

    def post(self, request):
        form = MaladieForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Maladie enregistrée avec succès.")
                return redirect("maladie:maladie_list")
            except ValidationError as e:
                if hasattr(e, "message_dict"):
                    for field, msgs in e.message_dict.items():
                        if isinstance(msgs, (list, tuple)):
                            for m in msgs:
                                messages.error(request, f"{field}: {m}")
                        else:
                            messages.error(request, f"{field}: {msgs}")
                else:
                    messages.error(request, str(e))
            except IntegrityError:
                messages.error(request, "Conflit d’unicité : un enregistrement identique existe déjà.")
            except Exception as e:
                messages.error(request, f"Erreur : {e}")
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    messages.error(request, f"{field}: {err}")

        return render(request, "maladie/form.html", {"form": form})


class MaladieUpdateView(View):
    def get(self, request, pk):
        maladie = get_object_or_404(Maladie, pk=pk)
        form = MaladieForm(instance=maladie)
        return render(request, "maladie/form.html", {"form": form, "maladie": maladie})

    def post(self, request, pk):
        maladie = get_object_or_404(Maladie, pk=pk)
        form = MaladieForm(request.POST, instance=maladie)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Maladie mise à jour.")
                return redirect("maladie:maladie_list")
            except ValidationError as e:
                if hasattr(e, "message_dict"):
                    for field, msgs in e.message_dict.items():
                        if isinstance(msgs, (list, tuple)):
                            for m in msgs:
                                messages.error(request, f"{field}: {m}")
                        else:
                            messages.error(request, f"{field}: {msgs}")
                else:
                    messages.error(request, str(e))
            except IntegrityError:
                messages.error(request, "Conflit d’unicité : un enregistrement identique existe déjà.")
            except Exception as e:
                messages.error(request, f"Erreur : {e}")
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    messages.error(request, f"{field}: {err}")

        return render(request, "maladie/form.html", {"form": form, "maladie": maladie})


class MaladieDeleteView(View):
    # Page de confirmation
    def get(self, request, pk):
        maladie = get_object_or_404(Maladie, pk=pk)
        return render(request, "maladie/confirm_suppression.html", {"maladie": maladie})

    # Suppression
    def post(self, request, pk):
        maladie = get_object_or_404(Maladie, pk=pk)
        try:
            maladie.delete()
            messages.success(request, "Enregistrement supprimé.")
        except Exception as e:
            messages.error(request, f"Suppression impossible : {e}")
        return redirect("maladie:maladie_list")


# ========= Tableau de bord (optionnel) =========
# Si tes templates utilisent `{% url 'maladie:dashboard' %}`, garde cette vue.
# Sinon, tu peux la supprimer et retirer le lien des templates.

def dashboard(request):
    total = Maladie.objects.count()
    par_statut = list(
        Maladie.objects.values("Statut").annotate(c=Count("id")).order_by("-c")
    )
    par_maladie = list(
        Maladie.objects.values("Nom_Maladie").annotate(c=Count("id")).order_by("-c")
    )
    derniers = (
        Maladie.objects
        .select_related("Boucle_Ovin")
        .order_by("-Date_observation", "-id")[:20]
    )

    return render(request, "maladie/dashboard.html", {
        "total": total,
        "par_statut": par_statut,
        "par_maladie": par_maladie,
        "derniers": derniers,
    })

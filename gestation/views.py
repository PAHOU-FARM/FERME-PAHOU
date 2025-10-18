# gestation/views.py
from datetime import date
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import IntegrityError
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404, render, redirect
from django.views import View

from .forms import GestationForm
from .models import Gestation


# ---------- Helpers ----------
def _parse_date(val):
    if not val:
        return None
    s = str(val).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            from datetime import datetime
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _filtered_queryset(request):
    """
    Filtres GET pris en charge :
      - q : recherche (boucle, méthode, état, observations)
      - etat : valeur exacte (Confirmée / Non Confirmée / À surveiller)
      - from / to : bornes de date_gestation
    """
    qs = Gestation.objects.select_related("boucle_brebis")

    q = (request.GET.get("q") or "").strip()
    etat = (request.GET.get("etat") or "").strip()
    dfrom = _parse_date(request.GET.get("from"))
    dto = _parse_date(request.GET.get("to"))

    if q:
        qs = qs.filter(
            Q(boucle_brebis__boucle_ovin__icontains=q)
            | Q(methode_confirmation__icontains=q)
            | Q(etat_gestation__icontains=q)
            | Q(observations__icontains=q)
        )

    if etat:
        qs = qs.filter(etat_gestation=etat)

    if dfrom:
        qs = qs.filter(date_gestation__gte=dfrom)
    if dto:
        qs = qs.filter(date_gestation__lte=dto)

    return qs.order_by("-date_gestation", "-id")


# ---------- Vues CRUD ----------
class GestationListView(View):
    def get(self, request):
        qs = _filtered_queryset(request)

        paginator = Paginator(qs, 20)
        page_number = request.GET.get("page", 1)
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        ctx = {
            "gestations": page_obj.object_list,
            "is_paginated": page_obj.has_other_pages(),
            "page_obj": page_obj,
            "filters": {
                "q": request.GET.get("q", ""),
                "etat": request.GET.get("etat", ""),
                "from": request.GET.get("from", ""),
                "to": request.GET.get("to", ""),
            },
        }
        return render(request, "gestation/liste.html", ctx)


class GestationDetailView(View):
    def get(self, request, pk):
        g = get_object_or_404(Gestation.objects.select_related("boucle_brebis"), pk=pk)
        return render(request, "gestation/detail.html", {"gestation": g})


class GestationCreateView(View):
    def get(self, request):
        form = GestationForm()
        return render(request, "gestation/form.html", {"form": form})

    def post(self, request):
        form = GestationForm(request.POST)
        if form.is_valid():
            try:
                obj = form.save()
                messages.success(request, "Gestation enregistrée avec succès.")
                return redirect("gestation:gestation_detail", pk=obj.pk)
            except ValidationError as e:
                if hasattr(e, "message_dict"):
                    for field, msgs in e.message_dict.items():
                        for m in (msgs if isinstance(msgs, (list, tuple)) else [msgs]):
                            messages.error(request, f"{field}: {m}")
                else:
                    messages.error(request, str(e))
            except IntegrityError:
                messages.error(request, "Un enregistrement existe déjà pour cette brebis à cette date.")
            except Exception as e:
                messages.error(request, f"Erreur : {str(e)}")
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    messages.error(request, f"{field}: {err}")
        return render(request, "gestation/form.html", {"form": form})


class GestationUpdateView(View):
    def get(self, request, pk):
        g = get_object_or_404(Gestation, pk=pk)
        form = GestationForm(instance=g)
        return render(request, "gestation/form.html", {"form": form, "gestation": g})

    def post(self, request, pk):
        g = get_object_or_404(Gestation, pk=pk)
        form = GestationForm(request.POST, instance=g)
        if form.is_valid():
            try:
                obj = form.save()
                messages.success(request, "Gestation mise à jour.")
                return redirect("gestation:gestation_detail", pk=obj.pk)
            except ValidationError as e:
                if hasattr(e, "message_dict"):
                    for field, msgs in e.message_dict.items():
                        for m in (msgs if isinstance(msgs, (list, tuple)) else [msgs]):
                            messages.error(request, f"{field}: {m}")
                else:
                    messages.error(request, str(e))
            except IntegrityError:
                messages.error(request, "Un enregistrement existe déjà pour cette brebis à cette date.")
            except Exception as e:
                messages.error(request, f"Erreur : {str(e)}")
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    messages.error(request, f"{field}: {err}")
        return render(request, "gestation/form.html", {"form": form, "gestation": g})


class GestationDeleteView(View):
    def get(self, request, pk):
        g = get_object_or_404(Gestation.objects.select_related("boucle_brebis"), pk=pk)
        return render(request, "gestation/confirm_suppression.html", {"gestation": g})

    def post(self, request, pk):
        g = get_object_or_404(Gestation, pk=pk)
        try:
            g.delete()
            messages.success(request, "Gestation supprimée.")
            return redirect("gestation:gestation_list")
        except Exception as e:
            messages.error(request, f"Suppression impossible : {str(e)}")
            return redirect("gestation:gestation_detail", pk=pk)


# ---------- Dashboard ----------
def dashboard(request):
    """
    Tableau de bord : on utilise la property modèle `date_estimee_mise_bas`
    (calculée) sans jamais filtrer/ordonner dessus côté ORM.
    """
    today = date.today()

    total = Gestation.objects.count()
    confirmees = Gestation.objects.filter(etat_gestation="Confirmée").count()
    non_confirmees = Gestation.objects.filter(etat_gestation="Non Confirmée").count()
    a_surveiller = Gestation.objects.filter(etat_gestation="A surveiller").count()

    par_etat = (
        Gestation.objects.values("etat_gestation")
        .annotate(c=Count("id"))
        .order_by("etat_gestation")
    )

    recentes = list(
        Gestation.objects.select_related("boucle_brebis")
        .order_by("-date_gestation", "-id")[:10]
    )
    # les templates peuvent lire g.date_estimee_mise_bas directement via la @property

    # Prochaines mises-bas : filtrage en Python, pas en base
    a_venir_list = []
    for g in Gestation.objects.select_related("boucle_brebis"):
        eta = g.date_estimee_mise_bas  # property du modèle
        if eta and eta >= today:
            a_venir_list.append(g)
    a_venir = sorted(a_venir_list, key=lambda x: x.date_estimee_mise_bas)[:10]

    ctx = {
        "total": total,
        "confirmees": confirmees,
        "non_confirmees": non_confirmees,
        "a_surveiller": a_surveiller,
        "par_etat": list(par_etat),
        "recentes": recentes,
        "a_venir": a_venir,
    }
    return render(request, "gestation/dashboard.html", ctx)

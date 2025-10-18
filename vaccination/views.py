# vaccination/views.py
from datetime import datetime
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import IntegrityError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from .models import Vaccination
from .forms import VaccinationForm


# ───────────────────────────
# Helpers
# ───────────────────────────
def _parse_date(val):
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
    Filtres pris en charge:
      - q           : boucle, type, nom, vétérinaire, observations
      - voie        : voie d’admin exacte
      - from / to   : bornes de dates (inclusives)
    """
    qs = Vaccination.objects.select_related("boucle_ovin").all()

    q = (request.GET.get("q") or "").strip()
    voie = (request.GET.get("voie") or "").strip()
    dfrom = _parse_date(request.GET.get("from"))
    dto = _parse_date(request.GET.get("to"))

    if q:
        qs = qs.filter(
            Q(boucle_ovin__boucle_ovin__icontains=q)
            | Q(type_vaccin__icontains=q)
            | Q(nom_vaccin__icontains=q)
            | Q(nom_veterinaire__icontains=q)
            | Q(observations__icontains=q)
        )
    if voie:
        qs = qs.filter(voie_administration=voie)
    if dfrom:
        qs = qs.filter(date_vaccination__gte=dfrom)
    if dto:
        qs = qs.filter(date_vaccination__lte=dto)

    return qs.order_by("-date_vaccination", "-id")


def _add_validation_messages(request, err: ValidationError):
    """
    Envoie proprement les messages issus d'un ValidationError,
    qu'il s'agisse d'un message_dict (par champs) ou d'une simple liste/chaîne.
    """
    if hasattr(err, "message_dict"):
        for field, msgs in err.message_dict.items():
            if isinstance(msgs, (list, tuple)):
                for m in msgs:
                    messages.error(request, f"{field}: {m}")
            else:
                messages.error(request, f"{field}: {msgs}")
    else:
        msgs = getattr(err, "messages", None)
        if msgs:
            for m in msgs:
                messages.error(request, m)
        else:
            messages.error(request, str(err))


# ───────────────────────────
# Vues
# ───────────────────────────
class VaccinationListView(View):
    paginate_by = 25  # Optionnel : pagination

    def get(self, request):
        qs = _filtered_qs(request)

        # Stats simples basées sur le résultat filtré
        total = qs.count()
        par_voie = list(qs.values("voie_administration").annotate(c=Count("id")).order_by("-c"))
        par_type = list(qs.values("type_vaccin").annotate(c=Count("id")).order_by("-c"))

        # Pagination (si tu ne l'utilises pas dans le template, rien ne casse)
        page_num = request.GET.get("page", 1)
        paginator = Paginator(qs, self.paginate_by)
        try:
            page_obj = paginator.page(page_num)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        ctx = {
            "vaccinations": page_obj.object_list,  # liste pour la page courante
            "page_obj": page_obj,
            "is_paginated": page_obj.has_other_pages(),
            "total": total,
            "par_voie": par_voie,
            "par_type": par_type,
            "filters": {
                "q": request.GET.get("q", ""),
                "voie": request.GET.get("voie", ""),
                "from": request.GET.get("from", ""),
                "to": request.GET.get("to", ""),
            },
        }
        return render(request, "vaccination/liste.html", ctx)


class VaccinationDetailView(View):
    def get(self, request, pk):
        obj = get_object_or_404(Vaccination.objects.select_related("boucle_ovin"), pk=pk)
        return render(request, "vaccination/detail.html", {"obj": obj})


class VaccinationCreateView(View):
    def get(self, request):
        form = VaccinationForm()
        return render(request, "vaccination/form.html", {"form": form})

    def post(self, request):
        form = VaccinationForm(request.POST)
        if form.is_valid():
            try:
                obj = form.save()
                messages.success(request, "Vaccination enregistrée avec succès.")
                return redirect("vaccination:vaccination_detail", pk=obj.pk)
            except ValidationError as e:
                _add_validation_messages(request, e)
            except IntegrityError:
                messages.error(
                    request,
                    "Un enregistrement identique (même ovin, même date, même vaccin) existe déjà."
                )
            except Exception as e:
                messages.error(request, f"Erreur : {e}")
        else:
            # Remonte aussi les erreurs de formulaire
            for field, errs in form.errors.items():
                for err in errs:
                    messages.error(request, f"{field}: {err}")

        return render(request, "vaccination/form.html", {"form": form})


class VaccinationUpdateView(View):
    def get(self, request, pk):
        obj = get_object_or_404(Vaccination, pk=pk)
        form = VaccinationForm(instance=obj)
        return render(request, "vaccination/form.html", {"form": form, "obj": obj})

    def post(self, request, pk):
        obj = get_object_or_404(Vaccination, pk=pk)
        form = VaccinationForm(request.POST, instance=obj)
        if form.is_valid():
            try:
                obj = form.save()
                messages.success(request, "Vaccination mise à jour.")
                return redirect("vaccination:vaccination_detail", pk=obj.pk)
            except ValidationError as e:
                _add_validation_messages(request, e)
            except IntegrityError:
                messages.error(
                    request,
                    "Un enregistrement identique (même ovin, même date, même vaccin) existe déjà."
                )
            except Exception as e:
                messages.error(request, f"Erreur : {e}")
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    messages.error(request, f"{field}: {err}")

        return render(request, "vaccination/form.html", {"form": form, "obj": obj})


class VaccinationDeleteView(View):
    def get(self, request, pk):
        obj = get_object_or_404(Vaccination, pk=pk)
        return render(request, "vaccination/confirm_suppression.html", {"obj": obj})

    def post(self, request, pk):
        obj = get_object_or_404(Vaccination, pk=pk)
        try:
            obj.delete()
            messages.success(request, "Vaccination supprimée.")
        except Exception as e:
            messages.error(request, f"Suppression impossible : {e}")
        return redirect("vaccination:vaccination_list")


def vaccination_dashboard(request):
    """
    Petit tableau de bord: compte total, top types, top voies, derniers enregistrements.
    """
    qs = Vaccination.objects.select_related("boucle_ovin").order_by("-date_vaccination", "-id")
    ctx = {
        "total": qs.count(),
        "par_type": list(qs.values("type_vaccin").annotate(c=Count("id")).order_by("-c")[:10]),
        "par_voie": list(qs.values("voie_administration").annotate(c=Count("id")).order_by("-c")),
        "derniers": list(qs[:20]),
    }
    return render(request, "vaccination/dashboard.html", ctx)

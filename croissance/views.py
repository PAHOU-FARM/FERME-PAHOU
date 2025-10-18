# croissance/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import TemplateView  # ✅ pour le dashboard
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from .models import Croissance
from .forms import CroissanceForm


class CroissanceListView(View):
    def get(self, request):
        """
        Liste simple, tri du plus récent, optimisée sur la FK.
        Filtres légers possibles : ?q=BOUCLE (contient).
        """
        qs = Croissance.objects.select_related('Boucle_Ovin').order_by('-Date_mesure', '-id')
        q = (request.GET.get('q') or '').strip()
        if q:
            qs = qs.filter(Boucle_Ovin__boucle_ovin__icontains=q)

        context = {
            'croissances': qs,
            'q': q,
        }
        return render(request, 'croissance/liste.html', context)


class CroissanceDetailView(View):
    def get(self, request, pk):
        obj = get_object_or_404(Croissance.objects.select_related('Boucle_Ovin'), pk=pk)
        return render(request, 'croissance/detail.html', {'obj': obj})


class CroissanceCreateView(View):
    def get(self, request):
        form = CroissanceForm()
        return render(request, 'croissance/form.html', {'form': form})

    def post(self, request):
        form = CroissanceForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Mesure de croissance enregistrée avec succès.")
                return redirect('croissance:croissance_list')
            except ValidationError as e:
                for field, msgs in e.message_dict.items():
                    for m in (msgs if isinstance(msgs, (list, tuple)) else [msgs]):
                        messages.error(request, f"{field}: {m}")
            except IntegrityError:
                messages.error(request, "Conflit d’unicité : une mesure (non historique) existe déjà pour cette date.")
            except Exception as e:
                messages.error(request, f"Erreur : {str(e)}")
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    messages.error(request, f"{field}: {err}")

        return render(request, 'croissance/form.html', {'form': form})


class CroissanceUpdateView(View):
    def get(self, request, pk):
        obj = get_object_or_404(Croissance, pk=pk)
        form = CroissanceForm(instance=obj)
        return render(request, 'croissance/form.html', {'form': form, 'obj': obj})

    def post(self, request, pk):
        obj = get_object_or_404(Croissance, pk=pk)
        form = CroissanceForm(request.POST, instance=obj)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Mesure mise à jour.")
                return redirect('croissance:croissance_list')
            except ValidationError as e:
                for field, msgs in e.message_dict.items():
                    for m in (msgs if isinstance(msgs, (list, tuple)) else [msgs]):
                        messages.error(request, f"{field}: {m}")
            except IntegrityError:
                messages.error(request, "Conflit d’unicité : une mesure (non historique) existe déjà pour cette date.")
            except Exception as e:
                messages.error(request, f"Erreur : {str(e)}")
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    messages.error(request, f"{field}: {err}")

        return render(request, 'croissance/form.html', {'form': form, 'obj': obj})


class CroissanceDeleteView(View):
    # Page de confirmation
    def get(self, request, pk):
        obj = get_object_or_404(Croissance.objects.select_related('Boucle_Ovin'), pk=pk)
        return render(request, 'croissance/confirm_suppression.html', {'obj': obj})

    # Suppression
    def post(self, request, pk):
        obj = get_object_or_404(Croissance, pk=pk)
        try:
            obj.delete()
            messages.success(request, "Mesure supprimée.")
        except Exception as e:
            messages.error(request, f"Suppression impossible : {str(e)}")
        return redirect('croissance:croissance_list')


# ✅ Dashboard (nécessaire pour l’URL 'croissance:croissance_dashboard')
class CroissanceDashboardView(TemplateView):
    template_name = "croissance/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # (facultatif) petites stats pour le template :
        qs = Croissance.objects.select_related('Boucle_Ovin')
        ctx["total"] = qs.count()
        ctx["dernieres"] = qs.order_by('-Date_mesure', '-id')[:10]
        return ctx

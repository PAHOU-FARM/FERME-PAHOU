from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from .forms import EmboucheForm
from .models import Embouche


# ========= Liste =========
class EmboucheListView(View):
    def get(self, request):
        embouches = (
            Embouche.objects
            .select_related('boucle_ovin')
            .order_by('-date_entree', '-id')
        )
        return render(request, 'embouche/liste.html', {'embouches': embouches})


# ========= Détail =========
class EmboucheDetailView(View):
    def get(self, request, pk):
        embouche = get_object_or_404(
            Embouche.objects.select_related('boucle_ovin'),
            pk=pk
        )
        return render(request, 'embouche/detail.html', {'embouche': embouche})


# ========= Création =========
class EmboucheCreateView(View):
    def get(self, request):
        form = EmboucheForm()
        return render(request, 'embouche/form.html', {'form': form})

    def post(self, request):
        form = EmboucheForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Embouche enregistrée avec succès.")
                return redirect('embouche:embouche_list')
            except ValidationError as e:
                # Erreurs de validation provenant du modèle (clean/constraints/signals)
                if hasattr(e, 'message_dict'):
                    for field, msgs in e.message_dict.items():
                        for m in (msgs if isinstance(msgs, (list, tuple)) else [msgs]):
                            messages.error(request, f"{field}: {m}")
                else:
                    messages.error(request, str(e))
            except IntegrityError:
                messages.error(
                    request,
                    "Conflit d’unicité : une embouche existe déjà pour cette date/ovin."
                )
            except Exception as e:
                messages.error(request, f"Erreur : {str(e)}")
        else:
            # Erreurs de formulaire
            for field, errs in form.errors.items():
                for err in errs:
                    messages.error(request, f"{field}: {err}")

        return render(request, 'embouche/form.html', {'form': form})


# ========= Modification =========
class EmboucheUpdateView(View):
    def get(self, request, pk):
        embouche = get_object_or_404(Embouche, pk=pk)
        form = EmboucheForm(instance=embouche)
        return render(request, 'embouche/form.html', {'form': form, 'embouche': embouche})

    def post(self, request, pk):
        embouche = get_object_or_404(Embouche, pk=pk)
        form = EmboucheForm(request.POST, instance=embouche)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Embouche mise à jour.")
                return redirect('embouche:embouche_list')
            except ValidationError as e:
                if hasattr(e, 'message_dict'):
                    for field, msgs in e.message_dict.items():
                        for m in (msgs if isinstance(msgs, (list, tuple)) else [msgs]):
                            messages.error(request, f"{field}: {m}")
                else:
                    messages.error(request, str(e))
            except IntegrityError:
                messages.error(
                    request,
                    "Conflit d’unicité : une embouche existe déjà pour cette date/ovin."
                )
            except Exception as e:
                messages.error(request, f"Erreur : {str(e)}")
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    messages.error(request, f"{field}: {err}")

        return render(request, 'embouche/form.html', {'form': form, 'embouche': embouche})


# ========= Suppression (avec confirmation) =========
class EmboucheDeleteView(View):
    def get(self, request, pk):
        embouche = get_object_or_404(Embouche.objects.select_related('boucle_ovin'), pk=pk)
        return render(request, 'embouche/confirm_suppression.html', {'embouche': embouche})

    def post(self, request, pk):
        embouche = get_object_or_404(Embouche, pk=pk)
        try:
            embouche.delete()
            messages.success(request, "Embouche supprimée.")
        except Exception as e:
            messages.error(request, f"Suppression impossible : {str(e)}")
        return redirect('embouche:embouche_list')


# ========= Dashboard =========
def dashboard(request):
    total = Embouche.objects.count()
    en_cours = Embouche.objects.filter(date_fin__isnull=True).count()
    terminees = Embouche.objects.filter(date_fin__isnull=False).count()

    agg = Embouche.objects.aggregate(
        duree_moy=Avg('duree'),
        gain_moy=Avg('poids_engraissement'),
    )

    repartition_proprietaire = (
        Embouche.objects.values('proprietaire')
        .annotate(c=Count('id'))
        .order_by('-c')
    )

    derniers = (
        Embouche.objects.select_related('boucle_ovin')
        .order_by('-date_entree', '-id')[:10]
    )

    context = {
        'stats': {
            'total': total,
            'en_cours': en_cours,
            'terminees': terminees,
            'duree_moy': agg['duree_moy'],
            'gain_moy': agg['gain_moy'],
        },
        'repartition_proprietaire': repartition_proprietaire,
        'derniers': derniers,
    }
    return render(request, 'embouche/dashboard.html', context)

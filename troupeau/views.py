# troupeau/views.py
from datetime import datetime
import csv
from io import TextIOWrapper, BytesIO

from django.contrib import messages
from django.db.models import Q, Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView

from .forms import TroupeauForm
from .models import Troupeau


# =========================
# Helpers internes
# =========================

def _parse_date(val):
    """Accepte 'YYYY-MM-DD' ou 'DD/MM/YYYY' -> date | None"""
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
    raise ValueError(f"Date invalide: {val} (formats attendus: YYYY-MM-DD ou DD/MM/YYYY)")


def _parse_float(val):
    """Accepte '12.3' ou '12,3' -> float | None"""
    if val is None:
        return None
    s = str(val).strip()
    if s == "":
        return None
    try:
        return float(s.replace(",", "."))
    except ValueError:
        raise ValueError(f"Nombre invalide: {val}")


# =========================
# Vues basées fonction
# =========================

def troupeau_formulaire(request):
    # Page “formulaire” simple (conservée si tu l’utilises encore)
    if request.method == 'POST':
        form = TroupeauForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Troupeau ajouté avec succès !")
            return redirect('troupeau:troupeau_formulaire')
        messages.error(request, "Erreur dans le formulaire. Vérifie les données.")
    else:
        form = TroupeauForm()

    recherche = (request.GET.get('recherche') or '').strip()
    if recherche:
        troupeaux = Troupeau.objects.filter(boucle_ovin__icontains=recherche)
    else:
        troupeaux = Troupeau.objects.all()

    return render(request, 'troupeau/troupeau_formulaire.html', {
        'form': form,
        'troupeaux': troupeaux,
        'recherche': recherche,
    })


def troupeau_genealogie(request, pk):
    """
    ✅ Conservation de l’URL historique mais redirection vers la fiche avec l’onglet 'généalogie'
    pour éviter un doublon d’écran.
    """
    url = reverse('troupeau:detail', kwargs={'pk': pk})
    return redirect(f"{url}?tab=genealogie")


def troupeau_descendants(request, pk):
    """
    ✅ Même principe : on redirige vers l’onglet 'descendance' de la fiche.
    """
    url = reverse('troupeau:detail', kwargs={'pk': pk})
    return redirect(f"{url}?tab=descendance")


def troupeau_reproducteurs(request):
    # Filtre DB par sexe + actif, puis filtre Python par âge de reproduction
    reproducteurs_qs = Troupeau.objects.filter(boucle_active=True, sexe='male')
    reproductrices_qs = Troupeau.objects.filter(boucle_active=True, sexe='femelle')
    reproducteurs = [a for a in reproducteurs_qs if getattr(a, 'is_reproducteur_age', False)]
    reproductrices = [a for a in reproductrices_qs if getattr(a, 'is_reproducteur_age', False)]
    return render(request, 'troupeau/reproducteurs.html', {
        'reproducteurs': reproducteurs,
        'reproductrices': reproductrices
    })


def rapport_consanguinite(request):
    animaux = Troupeau.objects.filter(coefficient_consanguinite__gt=0).order_by('-coefficient_consanguinite')
    return render(request, 'troupeau/rapport_consanguinite.html', {'animaux': animaux})


def troupeau_actions_masse(request):
    if request.method == 'POST':
        messages.info(request, "Aucune action de masse définie pour le moment.")
        return redirect('troupeau:liste')
    return render(request, 'troupeau/actions_masse.html')


def recalculer_consanguinite(request):
    if request.method == 'POST':
        for animal in Troupeau.objects.all():
            # la logique de recalcul peut être déclenchée dans save()
            animal.save()
        messages.success(request, 'Coefficients de consanguinité recalculés !')
        return redirect('troupeau:liste')
    return render(request, 'troupeau/confirm_recalcul.html')


def valider_donnees_troupeau(request):
    anomalies = []
    # Ex: doublons de boucle active
    doublons_actifs = (
        Troupeau.objects
        .filter(boucle_active=True)
        .values('boucle_ovin')
        .annotate(c=Count('id'))
        .filter(c__gt=1)
    )
    for d in doublons_actifs:
        anomalies.append(f"Boucle active dupliquée: {d['boucle_ovin']} ({d['c']} enregistrements)")
    return render(request, 'troupeau/validation_donnees.html', {'anomalies': anomalies})


def troupeau_dashboard(request):
    stats = {
        'total': Troupeau.objects.count(),
        'actifs': Troupeau.objects.filter(boucle_active=True).count(),
        'males': Troupeau.objects.filter(sexe='male').count(),
        'femelles': Troupeau.objects.filter(sexe='femelle').count(),
    }
    return render(request, 'troupeau/dashboard.html', {'stats': stats})


def troupeau_rapports(request):
    return render(request, 'troupeau/rapports.html')


def rapport_ages(request):
    return render(request, 'troupeau/rapport_ages.html')


def rapport_races(request):
    races = Troupeau.objects.values('race').annotate(count=Count('race'))
    return render(request, 'troupeau/rapport_races.html', {'races': races})


def rapport_reproducteurs(request):
    return render(request, 'troupeau/rapport_reproducteurs.html')


def import_troupeau(request):
    if request.method == 'POST' and request.FILES.get('fichier_import'):
        fichier = request.FILES['fichier_import']
        try:
            lignes = csv.DictReader(TextIOWrapper(fichier.file, encoding='utf-8'), delimiter=';')
            compteur = 0
            erreurs = []

            for ligne in lignes:
                try:
                    Troupeau.objects.create(
                        boucle_ovin=(ligne.get('boucle_ovin') or '').strip(),
                        sexe=(ligne.get('sexe') or '').strip(),
                        race=(ligne.get('race') or '').strip(),
                        naissance_date=_parse_date(ligne.get('naissance_date')),
                        statut=(ligne.get('statut') or '').strip(),
                        proprietaire_ovin=(ligne.get('proprietaire_ovin') or '').strip(),
                        origine_ovin=(ligne.get('origine_ovin') or '').strip(),
                        poids_initial=_parse_float(ligne.get('poids_initial')),
                        taille_initiale=_parse_float(ligne.get('taille_initiale')),
                        observations=(ligne.get('observations') or '').strip() or None
                    )
                    compteur += 1
                except Exception as e:
                    erreurs.append(f"Ligne {lignes.line_num}: {str(e)}")

            if erreurs:
                messages.warning(request, f"{compteur} animaux importés, {len(erreurs)} erreurs.")
                for erreur in erreurs[:5]:
                    messages.error(request, erreur)
            else:
                messages.success(request, f"{compteur} animaux importés avec succès !")

            return redirect('troupeau:liste')

        except Exception as e:
            messages.error(request, f"Erreur lors de l'import: {str(e)}")
            return redirect('troupeau:import')

    return render(request, 'troupeau/import.html')


def download_import_template(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="template_import_troupeau.csv"'
    writer = csv.writer(response, delimiter=';')
    writer.writerow([
        'boucle_ovin', 'sexe', 'race', 'naissance_date',
        'pere_boucle', 'mere_boucle', 'statut', 'proprietaire_ovin',
        'origine_ovin', 'poids_initial', 'taille_initiale', 'observations'
    ])
    return response


def export_troupeau_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="troupeau_export_{datetime.now().date()}.csv"'
    writer = csv.writer(response, delimiter=';')
    writer.writerow([
        'Numéro de boucle', 'Sexe', 'Race', 'Date de naissance',
        'Père', 'Mère', 'Statut', 'Propriétaire',
        'Coefficient de consanguinité', 'Remarques'
    ])
    for animal in Troupeau.objects.all().order_by('boucle_ovin'):
        writer.writerow([
            animal.boucle_ovin,
            getattr(animal, 'get_sexe_display', lambda: animal.sexe)(),
            getattr(animal, 'get_race_display', lambda: animal.race)(),
            animal.naissance_date.strftime('%d/%m/%Y') if animal.naissance_date else '',
            animal.pere_boucle.boucle_ovin if animal.pere_boucle else '',
            animal.mere_boucle.boucle_ovin if animal.mere_boucle else '',
            getattr(animal, 'get_statut_display', lambda: animal.statut)(),
            getattr(animal, 'get_proprietaire_ovin_display', lambda: animal.proprietaire_ovin)(),
            f"{animal.coefficient_consanguinite:.5f}".replace('.', ',') if animal.coefficient_consanguinite is not None else '',
            animal.observations or ''
        ])
    return response


def export_troupeau_excel(request):
    try:
        import openpyxl
    except ImportError:
        messages.error(request, "La fonctionnalité Excel nécessite la librairie openpyxl")
        return redirect('troupeau:liste')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Troupeau"
    ws.append([
        'Numéro de boucle', 'Sexe', 'Race', 'Date de naissance',
        'Père', 'Mère', 'Statut', 'Propriétaire',
        'Coefficient de consanguinité', 'Remarques'
    ])
    for animal in Troupeau.objects.all().order_by('boucle_ovin'):
        ws.append([
            animal.boucle_ovin,
            getattr(animal, 'get_sexe_display', lambda: animal.sexe)(),
            getattr(animal, 'get_race_display', lambda: animal.race)(),
            animal.naissance_date,
            animal.pere_boucle.boucle_ovin if animal.pere_boucle else '',
            animal.mere_boucle.boucle_ovin if animal.mere_boucle else '',
            getattr(animal, 'get_statut_display', lambda: animal.statut)(),
            getattr(animal, 'get_proprietaire_ovin_display', lambda: animal.proprietaire_ovin)(),
            float(f"{animal.coefficient_consanguinite:.5f}") if animal.coefficient_consanguinite is not None else 0.0,
            animal.observations or ''
        ])
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="troupeau_export_{datetime.now().date()}.xlsx"'
    response.write(buffer.read())
    return response


def export_troupeau_pdf(request):
    try:
        from django.template.loader import render_to_string
        from weasyprint import HTML
    except Exception:
        messages.error(request, "Export PDF indisponible (WeasyPrint manquant ?)")
        return redirect('troupeau:liste')

    animaux = Troupeau.objects.all().order_by('boucle_ovin')
    html_string = render_to_string('troupeau/export_pdf.html', {
        'animaux': animaux,
        'today': datetime.now()
    })
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=\"troupeau_export_{datetime.now().date()}.pdf\"'
    HTML(string=html_string).write_pdf(target=response)
    return response


# =========================
# Étiquettes (HTML/PDF)
# =========================

def generer_etiquettes(request):
    """
    ?ids=1,2,3 pour limiter aux IDs
    ?format=pdf pour export PDF (fallback HTML si erreur)
    """
    ids = (request.GET.get('ids') or '').strip()
    fmt = (request.GET.get('format') or 'html').lower()

    if ids:
        try:
            id_list = [int(x) for x in ids.split(',') if x.strip().isdigit()]
        except ValueError:
            id_list = []
        animaux = Troupeau.objects.filter(pk__in=id_list)
    else:
        animaux = Troupeau.objects.filter(boucle_active=True)

    animaux = animaux.order_by('boucle_ovin')
    context = {"animaux": animaux, "today": datetime.now()}

    if fmt == 'pdf':
        try:
            from django.template.loader import render_to_string
            from weasyprint import HTML

            html_string = render_to_string("troupeau/etiquettes.html", context)
            response = HttpResponse(content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename=\"etiquettes_{datetime.now().date()}.pdf\"'
            HTML(string=html_string).write_pdf(target=response)
            return response
        except Exception:
            pass  # fallback HTML

    return render(request, "troupeau/etiquettes.html", context)


def generer_etiquette_individuelle(request, pk):
    """
    ?format=pdf pour export PDF (fallback HTML si indisponible)
    """
    animal = get_object_or_404(Troupeau, pk=pk)
    fmt = (request.GET.get('format') or "html").lower()
    context = {"animal": animal, "today": datetime.now()}

    if fmt == "pdf":
        try:
            from django.template.loader import render_to_string
            from weasyprint import HTML

            html_string = render_to_string("troupeau/etiquette_individuelle.html", context)
            response = HttpResponse(content_type="application/pdf")
            filename = f"etiquette_{animal.boucle_ovin}_{datetime.now().date()}.pdf"
            response["Content-Disposition"] = f'attachment; filename=\"{filename}\"'
            HTML(string=html_string).write_pdf(target=response)
            return response
        except Exception:
            pass  # fallback HTML

    return render(request, "troupeau/etiquette_individuelle.html", context)


# =========================
# Vues génériques (CRUD)
# =========================

class TroupeauListView(ListView):
    model = Troupeau
    template_name = 'troupeau/liste.html'
    context_object_name = 'animaux'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related('pere_boucle', 'mere_boucle')

        q = (self.request.GET.get('q') or '').strip()
        if q:
            qs = qs.filter(
                Q(boucle_ovin__icontains=q) |
                Q(race__icontains=q) |
                Q(origine_ovin__icontains=q) |
                Q(statut__icontains=q)
            )

        # Filtre passé via extra_context dans urls.py (actifs, inactifs, males, femelles)
        extra = getattr(self, 'extra_context', None) or {}
        flt = extra.get('filter')
        if flt == 'actifs':
            qs = qs.filter(boucle_active=True)
        elif flt == 'inactifs':
            qs = qs.filter(boucle_active=False)
        elif flt == 'males':
            qs = qs.filter(sexe='male')
        elif flt == 'femelles':
            qs = qs.filter(sexe='femelle')

        return qs.order_by('boucle_ovin')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Stats rapides (utilisées par le template si présentes)
        ctx['stats'] = {
            'total': Troupeau.objects.count(),
            'actifs': Troupeau.objects.filter(boucle_active=True).count(),
            'males': Troupeau.objects.filter(sexe='male').count(),
            'femelles': Troupeau.objects.filter(sexe='femelle').count(),
        }
        return ctx


class TroupeauDetailView(DetailView):
    """
    ✅ FICHE UNIQUE AVEC ONGLET :
      - ?tab=profil (par défaut)
      - ?tab=genealogie
      - ?tab=descendance
    Les vues 'genealogie' et 'descendants' redirigent ici pour éviter les doublons.
    """
    model = Troupeau
    template_name = 'troupeau/detail.html'
    context_object_name = 'animal'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        a = self.object

        # Onglet actif
        tab = (self.request.GET.get('tab') or 'profil').lower()

        # Parents
        pere = a.pere_boucle
        mere = a.mere_boucle

        # Grands-parents (si disponibles)
        gp_pp = pere.pere_boucle if pere else None
        gp_pm = pere.mere_boucle if pere else None
        gp_mp = mere.pere_boucle if mere else None
        gp_mm = mere.mere_boucle if mere else None

        # Enfants directs (on ne dépend pas d'une méthode custom incertaine)
        enfants = Troupeau.objects.filter(
            Q(pere_boucle=a) | Q(mere_boucle=a)
        ).order_by('boucle_ovin')

        ctx.update({
            'active_tab': tab,
            'parents': {'pere': pere, 'mere': mere},
            'grands_parents': {
                'gp_pp': gp_pp, 'gp_pm': gp_pm,
                'gp_mp': gp_mp, 'gp_mm': gp_mm,
            },
            'enfants': enfants,
            'fa': getattr(a, 'coefficient_consanguinite', None),
        })
        return ctx


class TroupeauCreateView(CreateView):
    model = Troupeau
    form_class = TroupeauForm
    template_name = 'troupeau/form.html'
    success_url = reverse_lazy('troupeau:liste')

    def form_valid(self, form):
        messages.success(self.request, 'Animal ajouté avec succès !')
        return super().form_valid(form)


class TroupeauUpdateView(UpdateView):
    model = Troupeau
    form_class = TroupeauForm
    template_name = 'troupeau/form.html'
    context_object_name = 'animal'
    success_url = reverse_lazy('troupeau:liste')

    def form_valid(self, form):
        messages.success(self.request, 'Animal mis à jour avec succès !')
        return super().form_valid(form)


class TroupeauDeleteView(DeleteView):
    model = Troupeau
    template_name = 'troupeau/confirm_suppression.html'
    success_url = reverse_lazy('troupeau:liste')
    context_object_name = 'animal'

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Animal supprimé avec succès !')
        return super().delete(request, *args, **kwargs)


# =========================
# Vue ARBRE (TreeView)
# =========================

class TroupeauTreeView(TemplateView):
    """
    Vue hiérarchique (parents -> enfants).
    - On attache l’animal sous la mère si connue, sinon sous le père.
    - Racines = animaux sans parent connu.
    - Aplatissage DFS pour affichage tabulaire avec indentation.
    """
    template_name = 'troupeau/liste_tree.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        qs = (Troupeau.objects
              .select_related('pere_boucle', 'mere_boucle')
              .only('id', 'boucle_ovin', 'sexe', 'race', 'boucle_active',
                    'pere_boucle_id', 'mere_boucle_id'))

        # parent -> enfants
        children = {}
        for a in qs:
            parent_id = a.mere_boucle_id or a.pere_boucle_id
            if parent_id:
                children.setdefault(parent_id, []).append(a)

        # Racines
        roots = [a for a in qs if not (a.mere_boucle_id or a.pere_boucle_id)]

        # DFS d’aplatissement
        tree = []
        visited = set()

        def dfs(node, depth=0):
            if node.id in visited:
                return
            visited.add(node.id)
            tree.append({
                'animal': node,
                'depth': depth,
                'indent': depth * 18,  # px d’indentation
            })
            for child in sorted(children.get(node.id, []),
                                key=lambda x: (x.race or '', x.boucle_ovin or '')):
                dfs(child, depth + 1)

        for root in sorted(roots, key=lambda x: (x.race or '', x.boucle_ovin or '')):
            dfs(root, 0)

        # Stats rapides
        ctx['stats'] = {
            'total': qs.count(),
            'actifs': sum(1 for a in qs if a.boucle_active),
            'males': sum(1 for a in qs if (a.sexe or '').lower() in ('male', 'mâle')),
            'femelles': sum(1 for a in qs if (a.sexe or '').lower() in ('femelle',)),
        }
        ctx['tree'] = tree
        return ctx


# =========================
# Vues spécialisées simples
# =========================

def troupeau_jeunes(request):
    """Jeunes <= 12 mois (calcul Python via property age_en_mois)."""
    jeunes = [a for a in Troupeau.objects.all() if (getattr(a, 'age_en_mois', None) is not None and a.age_en_mois <= 12)]
    return render(request, 'troupeau/jeunes.html', {'jeunes': jeunes})


def troupeau_ages(request):
    ages = Troupeau.objects.order_by('-naissance_date')
    return render(request, 'troupeau/ages.html', {'ages': ages})


def troupeau_par_race(request, race):
    animaux = Troupeau.objects.filter(race=race).order_by('boucle_ovin')
    return render(request, 'troupeau/par_race.html', {'animaux': animaux, 'race': race})


def troupeau_par_proprietaire(request, proprietaire):
    animaux = Troupeau.objects.filter(proprietaire_ovin=proprietaire).order_by('boucle_ovin')
    return render(request, 'troupeau/par_proprietaire.html', {'animaux': animaux, 'proprietaire': proprietaire})


# =========================
# API & AJAX
# =========================

def api_recherche_animaux(request):
    """
    GET /api/recherche/?q=...
    Retourne une liste JSON d'animaux (id, boucle, sexe, race, statut, actif)
    """
    q = (request.GET.get('q') or '').strip()
    qs = Troupeau.objects.all()
    if q:
        qs = qs.filter(
            Q(boucle_ovin__icontains=q) |
            Q(race__icontains=q) |
            Q(origine_ovin__icontains=q) |
            Q(statut__icontains=q)
        )
    data = [{
        'id': a.id,
        'boucle_ovin': a.boucle_ovin,
        'sexe': a.sexe,
        'race': a.race,
        'statut': a.statut,
        'boucle_active': a.boucle_active
    } for a in qs.order_by('boucle_ovin')[:100]]
    return JsonResponse({'results': data})


def api_parents_disponibles(request):
    """
    GET /api/parents-disponibles/?exclude_id=<id>
    Retourne pères (mâles actifs) et mères (femelles actives).
    """
    exclude_id = request.GET.get('exclude_id')
    males = Troupeau.objects.filter(sexe='male', boucle_active=True)
    femelles = Troupeau.objects.filter(sexe='femelle', boucle_active=True)
    if exclude_id and str(exclude_id).isdigit():
        males = males.exclude(pk=int(exclude_id))
        femelles = femelles.exclude(pk=int(exclude_id))
    data = {
        'peres': [{'id': a.id, 'boucle_ovin': a.boucle_ovin} for a in males.order_by('boucle_ovin')],
        'meres': [{'id': a.id, 'boucle_ovin': a.boucle_ovin} for a in femelles.order_by('boucle_ovin')],
    }
    return JsonResponse(data)


def api_genealogie(request, pk):
    """
    GET /api/genealogie/<pk>/
    Retourne père, mère, enfants directs.
    """
    a = get_object_or_404(Troupeau, pk=pk)
    pere = a.pere_boucle
    mere = a.mere_boucle
    enfants_qs = Troupeau.objects.filter(Q(pere_boucle=a) | Q(mere_boucle=a)).order_by('boucle_ovin')
    data = {
        'id': a.id,
        'boucle_ovin': a.boucle_ovin,
        'pere': {'id': pere.id, 'boucle_ovin': pere.boucle_ovin} if pere else None,
        'mere': {'id': mere.id, 'boucle_ovin': mere.boucle_ovin} if mere else None,
        'enfants': [{'id': x.id, 'boucle_ovin': x.boucle_ovin} for x in enfants_qs],
    }
    return JsonResponse(data)


def api_valider_boucle(request):
    """
    GET /api/valider-boucle/?boucle=OV123&exclude_id=<id>
    Vérifie qu’aucun autre animal actif n’utilise cette boucle.
    """
    boucle = (request.GET.get('boucle') or '').strip()
    exclude_id = request.GET.get('exclude_id')

    if not boucle:
        return JsonResponse({'ok': False, 'error': 'Boucle manquante'}, status=400)

    qs = Troupeau.objects.filter(boucle_ovin__iexact=boucle, boucle_active=True)
    if exclude_id and str(exclude_id).isdigit():
        qs = qs.exclude(pk=int(exclude_id))

    if qs.exists():
        return JsonResponse({'ok': False, 'error': "Cette boucle est déjà active pour un autre animal."})

    inactifs = Troupeau.objects.filter(boucle_ovin__iexact=boucle, boucle_active=False).exists()
    return JsonResponse({'ok': True, 'info': 'Boucle réutilisable' if inactifs else 'Boucle disponible'})


def api_calculer_consanguinite(request):
    """
    GET /api/calculer-consanguinite/?pere_id=..&mere_id=..
    Calcule un coefficient hypothétique pour ce couple.
    """
    pere_id = request.GET.get('pere_id')
    mere_id = request.GET.get('mere_id')
    sexe = request.GET.get('sexe', 'male')
    race = request.GET.get('race', 'bali_bali')
    statut = request.GET.get('statut', 'naissance')
    origine = request.GET.get('origine_ovin', 'cotonou')
    proprietaire = request.GET.get('proprietaire_ovin', 'miguel')

    if not (pere_id and mere_id and str(pere_id).isdigit() and str(mere_id).isdigit()):
        return JsonResponse({'ok': False, 'error': 'pere_id et mere_id sont requis'}, status=400)

    pere = get_object_or_404(Troupeau, pk=int(pere_id))
    mere = get_object_or_404(Troupeau, pk=int(mere_id))

    temp = Troupeau(
        pere_boucle=pere,
        mere_boucle=mere,
        sexe=sexe,
        race=race,
        statut=statut,
        origine_ovin=origine,
        proprietaire_ovin=proprietaire
    )
    try:
        coeff = temp.coefficient_consanguinite_wright()
    except Exception:
        coeff = 0.0

    return JsonResponse({'ok': True, 'coefficient': coeff})


# --- Pont vers l'historique (lecture seule) ---

def troupeau_historique(request, pk):
    """
    Délègue à la vue liste lecture-seule des historiques pour un animal donné.
    Import local pour éviter les imports circulaires.
    """
    from historiquetroupeau.views import HistoriqueParTroupeauListView
    return HistoriqueParTroupeauListView.as_view()(request, pk=pk)

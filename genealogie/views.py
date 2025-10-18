from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.messages.views import SuccessMessageMixin

from .models import Genealogie
from .forms import GenealogieForm


class GenealogieListView(ListView):
    model = Genealogie
    template_name = "genealogie/liste.html"
    context_object_name = "genealogies"
    paginate_by = 25

    def get_queryset(self):
        return (
            Genealogie.objects
            .select_related("agneau", "mere", "pere")
            .order_by("-id")
        )


class GenealogieDetailView(DetailView):
    model = Genealogie
    template_name = "genealogie/detail.html"
    context_object_name = "g"


class GenealogieCreateView(SuccessMessageMixin, CreateView):
    model = Genealogie
    form_class = GenealogieForm
    template_name = "genealogie/form.html"
    success_url = reverse_lazy("genealogie:liste")
    success_message = "Généalogie enregistrée avec succès."


class GenealogieUpdateView(SuccessMessageMixin, UpdateView):
    model = Genealogie
    form_class = GenealogieForm
    template_name = "genealogie/form.html"
    success_url = reverse_lazy("genealogie:liste")
    success_message = "Généalogie mise à jour."


class GenealogieDeleteView(DeleteView):
    model = Genealogie
    template_name = "genealogie/confirm_suppression.html"
    success_url = reverse_lazy("genealogie:liste")

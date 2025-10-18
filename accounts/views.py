# accounts/views.py
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout, views as auth_views, get_user_model
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django.contrib.auth.views import PasswordResetConfirmView


class LoginViewCustom(auth_views.LoginView):
    """
    Vue de connexion personnalisée :
    - Déconnecte tout utilisateur déjà connecté avant d'afficher le login.
    - Empêche le cache et la mémorisation du mot de passe par le navigateur.
    - Redirige vers LOGIN_REDIRECT_URL ou ?next= après connexion.
    """
    template_name = "accounts/login.html"
    redirect_authenticated_user = False  # on gère nous-mêmes la déconnexion

    def get(self, request, *args, **kwargs):
        # 🔐 Déconnecte tout utilisateur connecté avant l’affichage du formulaire
        if request.user.is_authenticated:
            logout(request)

        response = super().get(request, *args, **kwargs)
        self._disable_browser_cache(response)
        return response

    def form_valid(self, form):
        """Connexion réussie : session fraîche + headers anti-cache."""
        response = super().form_valid(form)
        self.request.session["fresh_login"] = True
        messages.success(self.request, _("Bienvenue, %(user)s !") % {"user": self.request.user.username})
        self._disable_browser_cache(response)
        return response

    def get_success_url(self):
        """Redirige vers ?next= ou settings.LOGIN_REDIRECT_URL."""
        next_url = self.request.POST.get("next") or self.request.GET.get("next")
        return next_url or settings.LOGIN_REDIRECT_URL

    @staticmethod
    def _disable_browser_cache(response):
        """Ajoute des en-têtes pour éviter la mise en cache du navigateur."""
        response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response["Pragma"] = "no-cache"
        response["Expires"] = "0"
        return response


class AdminPasswordResetView(View):
    """
    Réinitialisation de mot de passe via e-mail, protégée par un 'code admin' si non-staff.
    - STAFF connecté : pas besoin de code.
    - Non-staff : doit fournir ADMIN_RESET_CODE (dans settings.py).
    - Message neutre pour éviter la fuite d'informations.
    """
    template_name = "accounts/password_reset_admin.html"
    neutral_msg = _("Si l’adresse existe, un e-mail de réinitialisation vient d’être envoyé.")

    def get(self, request):
        staff_ok = request.user.is_authenticated and request.user.is_staff
        response = render(request, self.template_name, {"require_code": not staff_ok})
        self._disable_browser_cache(response)
        return response

    @method_decorator(sensitive_post_parameters("admin_code", "email"))
    def post(self, request):
        admin_code = (request.POST.get("admin_code") or "").strip()
        target_email = (request.POST.get("email") or "").strip()

        staff_ok = request.user.is_authenticated and request.user.is_staff
        expected_code = getattr(settings, "ADMIN_RESET_CODE", "")

        # Vérifications
        if not staff_ok and not expected_code:
            messages.error(request, _("Configuration manquante : ADMIN_RESET_CODE."))
            return render(
                request, self.template_name, {"email": target_email, "require_code": True}
            )

        if not staff_ok and admin_code != expected_code:
            messages.error(request, _("Code administrateur invalide."))
            return render(
                request, self.template_name, {"email": target_email, "require_code": True}
            )

        # Lancer la réinitialisation standard
        form = PasswordResetForm({"email": target_email})
        if form.is_valid():
            form.save(
                request=request,
                use_https=request.is_secure(),
                email_template_name="accounts/password_reset_email.txt",
                subject_template_name="accounts/password_reset_subject.txt",
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            )

        messages.success(request, self.neutral_msg)
        return redirect("accounts:password_reset_done")

    @staticmethod
    def _disable_browser_cache(response):
        """Ajoute des en-têtes pour éviter la mise en cache du navigateur."""
        response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response["Pragma"] = "no-cache"
        response["Expires"] = "0"
        return response


class PasswordResetConfirmCustomView(PasswordResetConfirmView):
    """
    Vue personnalisée pour la réinitialisation du mot de passe via lien email.
    - Si le lien est invalide/expiré → redirection vers accounts:password_reset_invalid.
    - Applique les headers anti-cache.
    """
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")

    # --- Helpers privés ---
    def _disable_browser_cache(self, response):
        response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response["Pragma"] = "no-cache"
        response["Expires"] = "0"
        return response

    def _check_token_valid(self, uidb64, token):
        """
        Reproduit la vérification faite par PasswordResetConfirmView pour
        déterminer si le lien est encore valide.
        """
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = get_user_model()._default_manager.get(pk=uid)
        except Exception:
            return None, False

        is_valid = default_token_generator.check_token(user, token)
        return user, is_valid

    # --- GET/POST surchargés pour contrôler la validité AVANT le rendu ---
    def get(self, request, *args, **kwargs):
        user, is_valid = self._check_token_valid(kwargs.get("uidb64"), kwargs.get("token"))
        if not is_valid:
            messages.error(
                request,
                _("Le lien de réinitialisation est invalide ou a expiré. Veuillez en demander un nouveau.")
            )
            return redirect("accounts:password_reset_invalid")

        # Lien ok → laisser la vue parent construire le formulaire
        response = super().get(request, *args, **kwargs)
        return self._disable_browser_cache(response)

    def post(self, request, *args, **kwargs):
        user, is_valid = self._check_token_valid(kwargs.get("uidb64"), kwargs.get("token"))
        if not is_valid:
            messages.error(
                request,
                _("Le lien de réinitialisation est invalide ou a expiré. Veuillez en demander un nouveau.")
            )
            return redirect("accounts:password_reset_invalid")

        response = super().post(request, *args, **kwargs)
        return self._disable_browser_cache(response)

    def form_valid(self, form):
        """Mot de passe modifié avec succès → message + redirection."""
        messages.success(
            self.request,
            _("Votre mot de passe a été réinitialisé avec succès. Vous pouvez maintenant vous connecter.")
        )
        return super().form_valid(form)

# accounts/urls.py
from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required

from .views import (
    LoginViewCustom,
    AdminPasswordResetView,
    PasswordResetConfirmCustomView,  # Vue personnalisée pour le lien de réinitialisation
)

app_name = "accounts"

urlpatterns = [
    # --- Authentification ---
    path(
        "login/",
        LoginViewCustom.as_view(template_name="accounts/login.html"),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page=reverse_lazy("accounts:login")),
        name="logout",
    ),

    # --- Tableau de bord (protégé) ---
    path(
        "dashboard/",
        login_required(
            TemplateView.as_view(template_name="accounts/dashboard.html"),
            login_url=reverse_lazy("accounts:login"),
        ),
        name="dashboard",
    ),

    # --- Réinitialisation via code admin ---
    path(
        "password-reset-admin/",
        AdminPasswordResetView.as_view(),
        name="password_reset_admin",
    ),

    # --- Flux standard de réinitialisation de mot de passe ---
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html"
        ),
        name="password_reset_done",
    ),

    # Lien reçu par e-mail (utilise votre vue custom)
    path(
        "reset/<uidb64>/<token>/",
        PasswordResetConfirmCustomView.as_view(),
        name="password_reset_confirm",
    ),

    # Cas lien invalide/expiré (raccourci utilisé par la vue custom)
    path(
        "reset/invalid/",
        TemplateView.as_view(template_name="accounts/password_reset_invalid.html"),
        name="password_reset_invalid",
    ),

    # Fin du flux (succès)
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]

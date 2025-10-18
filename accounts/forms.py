# accounts/forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm

class LoginForm(AuthenticationForm):
    """
    Formulaire de connexion avec widgets Bootstrap.
    À brancher dans la vue : LoginViewCustom.form_class = LoginForm
    """
    username = forms.CharField(
        label="Nom d'utilisateur",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Nom d'utilisateur",
            "autofocus": "autofocus",
            "autocomplete": "username",
        }),
    )

    password = forms.CharField(
        label="Mot de passe",
        strip=False,
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Mot de passe",
            "autocomplete": "current-password",
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Supprime le suffixe de label (ex: ":") pour un rendu strict "Nom d'utilisateur" / "Mot de passe"
        self.label_suffix = ""

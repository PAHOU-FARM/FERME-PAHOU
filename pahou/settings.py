from pathlib import Path
import os
from django.urls import reverse_lazy

# === Chemins de base ===
BASE_DIR = Path(__file__).resolve().parent.parent

# === Sécurité / Débogage ===
DEBUG = os.environ.get("DEBUG", "True").lower() == "true"

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-dev-only-change-me"
)

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")

# === Auth / Redirections ===
LOGIN_URL = reverse_lazy("accounts:login")
LOGIN_REDIRECT_URL = reverse_lazy("accueil")
LOGOUT_REDIRECT_URL = reverse_lazy("accounts:login")

ADMIN_RESET_CODE = os.environ.get("ADMIN_RESET_CODE", "CHANGE-MOI-EN-PROD")

# === Applications ===
INSTALLED_APPS = [
    # Django apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Auth personnalisée
    "accounts",

    # Apps métier
    "troupeau.apps.TroupeauConfig",
    "historiquetroupeau.apps.HistoriquetroupeauConfig",
    "accouplement.apps.AccouplementConfig",
    "gestation.apps.GestationConfig",
    "naissance.apps.NaissanceConfig",
    "croissance.apps.CroissanceConfig",
    "reproduction.apps.ReproductionConfig",
    "embouche.apps.EmboucheConfig",
    "vaccination.apps.VaccinationConfig",
    "maladie.apps.MaladieConfig",
    "veterinaire.apps.VeterinaireConfig",
    "vente.apps.VenteConfig",
    "genealogie.apps.GenealogieConfig",
    "alimentation.apps.AlimentationConfig",
]

# === Middleware ===
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "pahou.urls"

# === Templates ===
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
            BASE_DIR / "pahou" / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "pahou.wsgi.application"

# === Base de données ===
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# === Validation des mots de passe ===
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# === Internationalisation / Fuseau ===
LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Africa/Lagos"
USE_I18N = True
USE_TZ = True

DATE_INPUT_FORMATS = ["%d/%m/%Y"]
DATE_FORMAT = "d/m/Y"

# === Fichiers statiques & médias ===
STATIC_URL = "/static/"
STATICFILES_DIRS = [
    BASE_DIR / "static",
    BASE_DIR / "pahou" / "static",
]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# === Emails ===
if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    DEFAULT_FROM_EMAIL = "no-reply@ferme-mv-pahou.local"
else:
    EMAIL_BACKEND = os.environ.get(
        "EMAIL_BACKEND",
        "django.core.mail.backends.smtp.EmailBackend"
    )
    EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.example.com")
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
    EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True").lower() == "true"
    DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "no-reply@ferme-mv-pahou.com")

# === Sessions ===
SESSION_EXPIRE_AT_BROWSER_CLOSE = True       # expire quand le navigateur se ferme
SESSION_COOKIE_AGE = 60 * 60 * 2             # 2 heures
SESSION_SAVE_EVERY_REQUEST = True            # prolonge la session à chaque action
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_ENGINE = "django.contrib.sessions.backends.db"

# === Logging minimal ===
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG" if DEBUG else "INFO",
    },
}

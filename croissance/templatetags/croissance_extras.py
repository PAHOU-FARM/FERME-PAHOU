from django import template
import unicodedata

register = template.Library()

def _norm(value: str) -> str:
    """Normalise : supprime accents, trim, lower."""
    if value is None:
        return ""
    s = str(value).strip()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return s.lower()

# Mapping vers les classes définies dans static/croissance/styles.css
_ETAT_MAP = {
    "bon": "etat-bon",
    "moyen": "etat-moyen",
    "mauvais": "etat-mauvais",
    "malade": "etat-malade",
}

_EVAL_MAP = {
    "normale": "eval-normale",
    "retard de croissance": "eval-retard",
    "retard": "eval-retard",
    "croissance acceleree": "eval-accelere",
    "acceleree": "eval-accelere",
}

@register.filter
def etat_badge_class(value: str) -> str:
    """
    Retourne la classe CSS pour l'état de santé.
    Ex: 'Bon' -> 'etat-bon'
    """
    return _ETAT_MAP.get(_norm(value), "")

@register.filter
def eval_badge_class(value: str) -> str:
    """
    Retourne la classe CSS pour l’évaluation de croissance.
    Ex: 'Retard de croissance' -> 'eval-retard'
    """
    return _EVAL_MAP.get(_norm(value), "")

@register.filter
def historic_row_class(is_histo: bool) -> str:
    """Ajoute 'is-histo' si enregistrement historique (pour griser la ligne)."""
    return "is-histo" if bool(is_histo) else ""

@register.filter
def float2(value) -> str:
    """Formate un nombre en 2 décimales ('' si None ou invalide)."""
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return ""

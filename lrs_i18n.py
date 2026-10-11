# lrs_i18n.py — langue de l'interface et des sorties (EN par défaut, FR en option).
#
# La langue arrive du front via l'en-tête X-LRS-Lang (voir pilot_static/i18n.js,
# qui l'ajoute à chaque fetch) et est posée dans un ContextVar par le
# middleware _require_auth de pilot_server.py. Le code appelé pendant la
# requête (audit_engine, PDF, diagnostics) lit get_lang() sans qu'on ait à
# faire descendre un paramètre dans chaque signature. Hors requête (audits
# planifiés en tâche de fond), on retombe sur la langue par défaut.
import contextvars

DEFAULT_LANG = "en"
SUPPORTED_LANGS = ("en", "fr")

_lang = contextvars.ContextVar("lrs_lang", default=DEFAULT_LANG)


def normalize_lang(value):
    value = (value or "").strip().lower()[:2]
    return value if value in SUPPORTED_LANGS else DEFAULT_LANG


def set_lang(value):
    _lang.set(normalize_lang(value))


def get_lang():
    return _lang.get()


def tr(fr, en):
    """Renvoie le texte FR ou EN selon la langue de la requête courante."""
    return fr if get_lang() == "fr" else en

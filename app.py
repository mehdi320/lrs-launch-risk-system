# LRS - Launch Risk System V2.5
# Paid Traffic Pre-Launch Audit Tool
# Built with Streamlit + OpenAI

import streamlit as st
import requests
import trafilatura
import json
import os
import datetime
import time
from html.parser import HTMLParser

try:
    from lrs_pdf_report import generate_pdf_report
    PDF_AVAILABLE = True
except Exception:
    PDF_AVAILABLE = False

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

APP_VERSION    = "2.8"
MAX_PAGE_CHARS = 8000

st.set_page_config(
    page_title="LRS - Launch Risk System",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS GLOBAL ───────────────────────────────────────────────
_DARK_VARS = """
    --bg-base: #07071a;
    --bg-card: #0f0f1a;
    --bg-card2: #1a1a2e;
    --bg-input: #0f0f1a;
    --border: #1e1e3a;
    --border2: #2a2a4a;
    --text-primary: #e0e0e0;
    --text-secondary: #aaa;
    --text-muted: #666;
    --tab-bg: #0f0f1a;
    --tab-active: #1a1a2e;
    --expander-bg: #0f0f1a;
    --expander-content: #0a0a14;
    --caption-color: #666;
    --streamlit-bg: #07071a;
"""
_LIGHT_VARS = """
    --bg-base: #f4f4f8;
    --bg-card: #ffffff;
    --bg-card2: #f0f0f8;
    --bg-input: #ffffff;
    --border: #dde0ef;
    --border2: #c8cbdf;
    --text-primary: #1a1a2e;
    --text-secondary: #444;
    --text-muted: #888;
    --tab-bg: #e8e8f0;
    --tab-active: #ffffff;
    --expander-bg: #ffffff;
    --expander-content: #f8f8fc;
    --caption-color: #888;
    --streamlit-bg: #f4f4f8;
"""

_CSS_TEMPLATE = """
<style>
:root { VARS_PLACEHOLDER }

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background-color: var(--bg-base) !important;
    color: var(--text-primary) !important;
}
h1, h2, h3 { letter-spacing: -0.3px; color: var(--text-primary) !important; }

#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    max-width: 1100px !important;
    background-color: var(--bg-base) !important;
}
.main { background-color: var(--bg-base) !important; }
.stApp { background-color: var(--bg-base) !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: var(--tab-bg);
    padding: 6px 8px;
    border-radius: 12px;
    border: 1px solid var(--border);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 8px 18px;
    font-size: 0.85rem;
    font-weight: 500;
    color: var(--text-muted) !important;
    background: transparent !important;
    border: none !important;
}
.stTabs [aria-selected="true"] {
    background: var(--tab-active) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border2) !important;
}

/* ── Buttons ── */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    transition: all 0.15s ease !important;
    border: 1px solid var(--border2) !important;
    background: var(--bg-card) !important;
    color: var(--text-primary) !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
    border-color: #6366f1 !important;
    color: #fff !important;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #7c7ff7, #6366f1) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 15px rgba(99,102,241,0.35) !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background: var(--bg-input) !important;
    border: 1px solid var(--border2) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
    font-size: 0.88rem !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 2px rgba(99,102,241,0.2) !important;
}

/* ── Labels ── */
.stTextInput label, .stTextArea label, .stSelectbox label,
.stRadio label, .stFileUploader label {
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    color: var(--text-secondary) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}

/* ── Expanders ── */
.streamlit-expanderHeader {
    background: var(--expander-bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    color: var(--text-secondary) !important;
}
.streamlit-expanderContent {
    background: var(--expander-content) !important;
    border: 1px solid var(--border) !important;
    border-top: none !important;
    border-radius: 0 0 8px 8px !important;
}

/* ── Métriques ── */
[data-testid="metric-container"] {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px 16px;
}
[data-testid="metric-container"] label {
    color: var(--text-secondary) !important;
    font-size: 0.75rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    color: var(--text-primary) !important;
}

/* ── Dataframes ── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
}

/* ── Info / Warning / Error ── */
.stInfo, .stSuccess, .stWarning, .stError {
    border-radius: 8px !important;
    font-size: 0.88rem !important;
}

/* ── Progress bar ── */
.stProgress > div > div > div {
    background: linear-gradient(90deg, #6366f1, #22c55e) !important;
    border-radius: 4px !important;
}

/* ── Download button ── */
.stDownloadButton > button {
    background: var(--bg-card) !important;
    border: 1px solid var(--border2) !important;
    border-radius: 8px !important;
    color: var(--text-secondary) !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
}
.stDownloadButton > button:hover {
    border-color: #6366f1 !important;
    color: var(--text-primary) !important;
}

/* ── Divider ── */
hr { border-color: var(--border) !important; margin: 1rem 0 !important; }

/* ── Caption ── */
.stCaption { color: var(--caption-color) !important; font-size: 0.78rem !important; }

/* ── Sidebar (cachée par défaut) ── */
[data-testid="stSidebar"] { display: none; }
</style>
"""

def inject_css(light_mode=False):
    vars_block = _LIGHT_VARS if light_mode else _DARK_VARS
    css = _CSS_TEMPLATE.replace("VARS_PLACEHOLDER", vars_block)
    st.markdown(css, unsafe_allow_html=True)

# ── CVR BENCHMARKS ──────────────────────────────────────────
CVR_BENCHMARKS = {
    "Digital product": {
        0: ("0.3-0.8%", "0.8-1.5%",  "+0.3 a +0.8 pts"),
        1: ("0.8-1.5%", "1.5-2.5%",  "+0.5 a +1.5 pts"),
        2: ("1.5-2.5%", "2.5-4.0%",  "+1.0 a +2.0 pts"),
        3: ("2.0-3.5%", "3.5-5.5%",  "+1.5 a +2.5 pts"),
    },
    "Ecom (produit physique)": {
        0: ("0.5-1.0%", "1.0-2.0%",  "+0.5 a +1.0 pts"),
        1: ("1.0-2.0%", "2.0-3.5%",  "+0.8 a +1.5 pts"),
        2: ("2.0-3.5%", "3.5-5.5%",  "+1.0 a +2.5 pts"),
        3: ("3.5-5.5%", "5.5-8.0%",  "+1.5 a +3.0 pts"),
    },
}

def get_tier(score):
    if score <= 9:  return 0
    if score <= 12: return 1
    if score <= 16: return 2
    return 3

def get_decision(score):
    if score <= 9:  return "Do NOT launch", "High"
    if score <= 14: return "Test small budget", "Moderate"
    return "Ready to scale", "Low"

# ── PERSISTANCE ──────────────────────────────────────────────
HISTORY_FILE   = os.path.join(os.path.dirname(__file__), ".lrs_history.json")
PROFILES_FILE  = os.path.join(os.path.dirname(__file__), ".lrs_profiles.json")
PROJECTS_FILE  = os.path.join(os.path.dirname(__file__), ".lrs_projects.json")
SCHEDULE_FILE  = os.path.join(os.path.dirname(__file__), ".lrs_schedule.json")
ONBOARDING_FILE= os.path.join(os.path.dirname(__file__), ".lrs_onboarded.json")

def load_history_file():
    """Charge l'historique depuis le fichier JSON (persistant entre sessions)."""
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Nettoyer les entrées sans champ 'result' (compatibilité)
                return [e for e in data if isinstance(e, dict)]
    except Exception:
        pass
    return []

def write_history_file(history):
    """Sauvegarde l'historique dans le fichier JSON."""
    try:
        # Ne pas sérialiser la clé _c (données calculées côté code, pas JSON-safe à 100%)
        clean = []
        for entry in history:
            e = {k: v for k, v in entry.items() if k != "result"}
            # Garder result mais sans _c
            if "result" in entry:
                r = {k: v for k, v in entry["result"].items() if k != "_c"}
                e["result"] = r
            clean.append(e)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(clean[:50], f, ensure_ascii=False, indent=2)
    except Exception:
        pass  # Silencieux si pas de droits d'écriture (Streamlit Cloud)

# ── PROFILS SAUVEGARDÉS ──────────────────────────────────────
def load_profiles():
    try:
        if os.path.exists(PROFILES_FILE):
            with open(PROFILES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_profiles(profiles):
    try:
        with open(PROFILES_FILE, "w", encoding="utf-8") as f:
            json.dump(profiles, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def save_profile(name, config):
    profiles = load_profiles()
    profiles[name] = config
    save_profiles(profiles)

def delete_profile(name):
    profiles = load_profiles()
    profiles.pop(name, None)
    save_profiles(profiles)

# ── AUDITS PLANIFIÉS ─────────────────────────────────────────
def load_schedule():
    try:
        if os.path.exists(SCHEDULE_FILE):
            with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_schedule(schedule):
    try:
        with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
            json.dump(schedule, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ── ONBOARDING ───────────────────────────────────────────────
def is_onboarded():
    try:
        if os.path.exists(ONBOARDING_FILE):
            return True
    except Exception:
        pass
    return False

def mark_onboarded():
    try:
        with open(ONBOARDING_FILE, "w", encoding="utf-8") as f:
            json.dump({"done": True, "date": datetime.datetime.now().strftime("%d/%m/%Y")}, f)
    except Exception:
        pass

# ── PROJETS MULTI-PAGES ──────────────────────────────────────
def load_projects():
    try:
        if os.path.exists(PROJECTS_FILE):
            with open(PROJECTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_projects(projects):
    try:
        with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
            json.dump(projects, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ── SESSION STATE ────────────────────────────────────────────
def init_session():
    if "audit_history" not in st.session_state:
        st.session_state.audit_history = load_history_file()
    if "loaded_result" not in st.session_state:
        st.session_state.loaded_result = None
    if "reaudit_url" not in st.session_state:
        st.session_state.reaudit_url = ""
    if "profiles" not in st.session_state:
        st.session_state.profiles = load_profiles()
    if "projects" not in st.session_state:
        st.session_state.projects = load_projects()
    if "impl_tracker" not in st.session_state:
        st.session_state.impl_tracker = {}
    if "schedule" not in st.session_state:
        st.session_state.schedule = load_schedule()
    if "onboarded" not in st.session_state:
        st.session_state.onboarded = is_onboarded()
    if "scheduled_ran" not in st.session_state:
        st.session_state.scheduled_ran = False  # éviter double run par session
    if "bulk_results" not in st.session_state:
        st.session_state.bulk_results = []
    if "score_alerts" not in st.session_state:
        st.session_state.score_alerts = []
    if "auto_reaudit_idx" not in st.session_state:
        st.session_state.auto_reaudit_idx = None
    if "light_mode" not in st.session_state:
        st.session_state.light_mode = False

def save_history(result, meta):
    entry = {**meta, "score": result.get("_c", {}).get("score", 0),
             "decision": result.get("_c", {}).get("decision", ""), "result": result}
    st.session_state.audit_history.insert(0, entry)
    if len(st.session_state.audit_history) > 50:
        st.session_state.audit_history = st.session_state.audit_history[:50]
    # Persister sur disque
    write_history_file(st.session_state.audit_history)

# ── SCHEDULER : vérif au démarrage ──────────────────────────
def run_scheduled_audits():
    """
    Vérifie les audits planifiés et exécute ceux dont la date est dépassée.
    Appelé une fois par session (guard via scheduled_ran).
    """
    schedule = st.session_state.schedule
    if not schedule:
        return

    now = datetime.datetime.now()
    ran_any = False

    for sid, sched in list(schedule.items()):
        if not sched.get("enabled", True):
            continue
        last_run_str = sched.get("last_run", "")
        freq_days    = int(sched.get("freq_days", 7))
        try:
            last_run = datetime.datetime.strptime(last_run_str, "%d/%m/%Y %H:%M") if last_run_str else datetime.datetime(2000, 1, 1)
        except Exception:
            last_run = datetime.datetime(2000, 1, 1)

        delta_days = (now - last_run).days
        if delta_days < freq_days:
            continue

        url = sched.get("url", "")
        if not url:
            continue

        # Lancer l'audit silencieusement
        try:
            content, status, is_js = extract_page(url)
            if not content:
                schedule[sid]["last_error"] = status
                schedule[sid]["last_run"]   = now.strftime("%d/%m/%Y %H:%M")
                continue
            pt  = detect_page_type(content, url)
            pl  = detect_language(content)
            res = run_audit(
                sched.get("mode", "Funnel Only"),
                sched.get("platform", "Meta"),
                sched.get("offer_type", "Digital product"),
                content, "",
                sched.get("market_context", ""),
                "gpt-4o-mini",
                brand_type=sched.get("brand_type", "Nouveau lancement"),
                page_type=pt, page_lang=pl,
            )
            ts   = now.strftime("%d/%m/%Y %H:%M")
            meta = {"url": url, "mode": sched.get("mode","Funnel Only"),
                    "platform": sched.get("platform","Meta"),
                    "offer_type": sched.get("offer_type","Digital product"),
                    "brand_type": sched.get("brand_type","Nouveau lancement"),
                    "page_type": pt, "timestamp": ts,
                    "scheduled": True}
            save_history(res, meta)
            schedule[sid]["last_run"]    = ts
            schedule[sid]["last_error"]  = ""
            schedule[sid]["last_score"]  = res.get("_c", {}).get("score", 0)
            ran_any = True
        except Exception as e:
            schedule[sid]["last_error"] = str(e)
            schedule[sid]["last_run"]   = now.strftime("%d/%m/%Y %H:%M")

    if ran_any:
        save_schedule(schedule)
        st.session_state.schedule = schedule

def compute_score_alerts(history):
    """
    Analyse l'historique et retourne une liste d'alertes (drops / progressions).
    Regroupe par URL, compare le dernier audit au précédent.
    """
    if len(history) < 2:
        return []
    url_map = {}
    for entry in reversed(history):  # du plus ancien au plus récent
        url = entry.get("url", "")
        if not url:
            continue
        if url not in url_map:
            url_map[url] = []
        url_map[url].append(entry)

    alerts = []
    for url, entries in url_map.items():
        if len(entries) < 2:
            continue
        latest = entries[-1]
        prev   = entries[-2]
        delta  = latest.get("score", 0) - prev.get("score", 0)
        if abs(delta) >= 2:   # seuil : changement significatif
            alerts.append({
                "url": url,
                "latest_score": latest.get("score", 0),
                "prev_score":   prev.get("score", 0),
                "delta":        delta,
                "latest_ts":    latest.get("timestamp", ""),
                "direction":    "up" if delta > 0 else "down",
            })
    # Trier par amplitude décroissante
    alerts.sort(key=lambda a: abs(a["delta"]), reverse=True)
    return alerts

# ── CHARGEMENT TXT ───────────────────────────────────────────
def load_txt(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""

# ── EXTRACTION PAGE WEB ──────────────────────────────────────
def clamp(text, n=MAX_PAGE_CHARS):
    return text[:n] + "[TRONQUE]" if len(text) > n else text

def detect_language(text: str) -> str:
    """Détection simple de la langue dominante de la page (fr / en / autre)."""
    sample = text[:3000].lower()
    fr_words = ["le ", "la ", "les ", "de ", "du ", "des ", "un ", "une ", "est ", "sont ",
                "avec ", "pour ", "dans ", "vous ", "nous ", "votre ", "notre "]
    en_words = ["the ", "and ", "with ", "for ", "your ", "our ", "this ", "that ", "from ",
                "you ", "are ", "have ", "will ", "more ", "can ", "all ", "free "]
    fr_count = sum(sample.count(w) for w in fr_words)
    en_count = sum(sample.count(w) for w in en_words)
    if fr_count == 0 and en_count == 0:
        return "autre"
    if en_count > fr_count * 1.5:
        return "en"
    if fr_count > en_count * 1.5:
        return "fr"
    return "mixte"

def check_js_heavy(html: str, extracted: str) -> bool:
    """Retourne True si la page semble être une SPA / rendue en JavaScript."""
    if len(extracted) < 400 and len(html) > 5000:
        return True
    js_signals = ["__next", "__nuxt", "react-root", "ng-version", "data-reactroot",
                  "window.__INITIAL_STATE__", "window.__PRELOADED_STATE__", "_app.js",
                  "chunk.js", "bundle.js"]
    html_low = html[:10000].lower()
    return sum(1 for s in js_signals if s in html_low) >= 2

def extract_page(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        html = r.text
    except requests.exceptions.ConnectionError:
        return "", "Impossible de se connecter.", False
    except requests.exceptions.Timeout:
        return "", "Timeout.", False
    except Exception as e:
        return "", str(e), False

    extracted = trafilatura.extract(html, include_links=False, include_images=False, no_fallback=False)
    is_js = check_js_heavy(html, extracted or "")

    if extracted and len(extracted.strip()) > 200:
        # Priorité above-the-fold : mettre les 2000 premiers caractères en tête
        full = extracted.strip()
        above_fold = full[:2000]
        rest       = full[2000:]
        prioritized = (
            "=== CONTENU ABOVE THE FOLD (prioritaire) ===\n" + above_fold +
            ("\n\n=== SUITE DE LA PAGE ===\n" + rest if rest else "")
        )
        return clamp(prioritized), f"Contenu extrait ({len(full[:MAX_PAGE_CHARS])} caracteres)", is_js

    class HP(HTMLParser):
        def __init__(self):
            super().__init__()
            self.parts, self.skip = [], False
            self.skip_tags = {"script", "style", "nav", "footer", "head"}
        def handle_starttag(self, tag, attrs):
            if tag in self.skip_tags: self.skip = True
        def handle_endtag(self, tag):
            if tag in self.skip_tags: self.skip = False
        def handle_data(self, data):
            t = data.strip()
            if not self.skip and len(t) > 20: self.parts.append(t)

    try:
        p = HP(); p.feed(html)
        fb = "\n".join(p.parts)
        if len(fb) > 100:
            return clamp(fb), f"Extraction partielle ({len(fb[:MAX_PAGE_CHARS])} caracteres)", is_js
    except Exception:
        pass

    return html[:2000], "Extraction faible.", True  # Si on arrive ici c'est probablement JS

# ── DETECTION TYPE DE PAGE ────────────────────────────────────
def detect_page_type(content: str, url: str = "") -> str:
    """
    Analyse le contenu scrape et l'URL pour identifier le type de page.
    Retourne une classification avec niveau de confiance.
    """
    if not content:
        return "Type inconnu (page vide)"

    text = content.lower()
    url_l = url.lower()

    # ── Détection prioritaire par URL (règles strictes) ──────
    import re

    # Page produit individuelle (ex: /products/nom-produit, /p/ref, /item/)
    product_page_patterns = [
        r"/products?/[^/]+/?$",         # /products/nom ou /product/nom
        r"/p/[^/]+/?$",                  # /p/ref
        r"/item/[^/]+/?$",               # /item/ref
        r"/shop/[^/]+/[^/]+/?$",         # /shop/category/produit
        r"/articles?/[^/]+/?$",          # /article/nom (some ecom)
        r"[?&](product|sku|pid|ref)=",   # paramètre produit
    ]
    for pattern in product_page_patterns:
        if re.search(pattern, url_l):
            # Confirmer avec contenu (éviter les faux positifs)
            product_confirm = ["ajouter au panier", "add to cart", "acheter", "buy",
                               "taille", "couleur", "size", "color", "quantite", "qty",
                               "en stock", "in stock", "livraison", "shipping", "avis", "reviews"]
            if sum(1 for s in product_confirm if s in text) >= 2:
                return "Page Produit Ecom (fiche produit individuelle) (confiance : haute)"

    # Catalogue / collection (ex: /collections/all, /shop, /boutique)
    catalogue_url_patterns = [r"/collections?/", r"/categor", r"/boutique/?$",
                               r"/shop/?$", r"/store/?$", r"/magasin"]
    for pattern in catalogue_url_patterns:
        if re.search(pattern, url_l):
            return "Page Catalogue Ecom (plusieurs produits) (confiance : haute)"

    # Blog / article
    blog_url_patterns = [r"/blog/", r"/articles?/", r"/posts?/", r"/actualite",
                         r"/news/", r"/magazine/"]
    for pattern in blog_url_patterns:
        if re.search(pattern, url_l):
            return "Blog / Article (confiance : haute)"

    # Homepage stricte (domaine seul ou avec juste une langue)
    url_path = re.sub(r"https?://[^/]+", "", url_l).rstrip("/")
    if url_path in ("", "/", "/fr", "/en", "/fr/", "/en/"):
        return "Page d'accueil / Homepage (confiance : haute)"

    # ── Scoring par contenu (si URL ne suffit pas) ───────────
    scores = {
        "Page Produit Ecom (fiche produit individuelle)": 0,
        "Sales Page / Landing Page (offre unique)": 0,
        "Page Catalogue Ecom (plusieurs produits)": 0,
        "Page SaaS / Logiciel": 0,
        "Page d'accueil / Homepage": 0,
        "Blog / Article": 0,
        "Page Lead Gen (capture email)": 0,
    }

    # Signaux Page Produit Ecom
    product_signals = ["ajouter au panier", "add to cart", "taille", "couleur", "size",
                       "color", "quantite", "qty", "en stock", "rupture de stock",
                       "livraison sous", "retours gratuits", "materiau", "composition",
                       "guide des tailles", "size guide", "avis verifies", "note globale",
                       "recommandent ce produit", "achetez avec"]
    scores["Page Produit Ecom (fiche produit individuelle)"] += sum(2 for s in product_signals if s in text)

    # Signaux Sales Page / Landing Page
    sales_signals = ["commander maintenant", "achetez maintenant", "buy now", "offre limitee",
                     "bonus", "valeur totale", "ce que vous obtenez", "what you get",
                     "place limitee", "testimonial", "100% satisfait", "garantie remboursement",
                     "sans risque", "prix special", "formation", "programme", "module",
                     "resultats", "transformation", "methode", "systeme"]
    scores["Sales Page / Landing Page (offre unique)"] += sum(2 for s in sales_signals if s in text)

    # Signaux Catalogue
    catalogue_signals = ["filtrer", "trier par", "filter by", "sort by", "nos produits",
                         "shop all", "toute la collection", "voir tous", "categories",
                         "nouveautes", "meilleures ventes", "best sellers", "promotions"]
    scores["Page Catalogue Ecom (plusieurs produits)"] += sum(2 for s in catalogue_signals if s in text)

    # Signaux SaaS
    saas_signals = ["essai gratuit", "free trial", "pricing", "tarifs", "plans",
                    "fonctionnalites", "features", "integrations", "api", "dashboard",
                    "abonnement", "per month", "par mois", "demo", "book a demo",
                    "logiciel", "software", "automatiser", "automatisation"]
    scores["Page SaaS / Logiciel"] += sum(2 for s in saas_signals if s in text)

    # Signaux Homepage
    home_signals = ["notre mission", "qui sommes-nous", "about us", "decouvrez nos",
                    "notre histoire", "we are", "bienvenue", "nos valeurs", "notre equipe"]
    scores["Page d'accueil / Homepage"] += sum(1 for s in home_signals if s in text)

    # Signaux Blog
    blog_signals = ["min de lecture", "minute read", "publie le", "par l'auteur",
                    "commentaires", "partager cet article", "share this", "lire la suite",
                    "read more", "tags:", "categorie:", "auteur:"]
    scores["Blog / Article"] += sum(2 for s in blog_signals if s in text)

    # Signaux Lead Gen
    leadgen_signals = ["entrez votre email", "enter your email", "inscrivez-vous gratuitement",
                       "telechargez", "download", "guide gratuit", "free guide", "webinar",
                       "masterclass", "challenge", "liste d'attente", "waitlist",
                       "acces immediat", "immediate access"]
    scores["Page Lead Gen (capture email)"] += sum(2 for s in leadgen_signals if s in text)

    # Determiner le type dominant
    best_type = max(scores, key=lambda k: scores[k])
    best_score = scores[best_type]

    if best_score < 2:
        return "Type non determine — scoring applique comme Sales Page standard"

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    second_score = sorted_scores[1][1] if len(sorted_scores) > 1 else 0
    confidence = "haute" if best_score >= 6 and best_score > second_score * 1.5 else "moderee"

    return f"{best_type} (confiance : {confidence})"

# ── PROMPT SYSTEME ───────────────────────────────────────────
SYSTEM_PROMPT_BASE = (
    "Tu es LRS - Launch Risk System V2, un auditeur paid traffic senior.\n"
    "LANGUE : Reponds TOUJOURS en francais. Tous les textes du JSON en francais.\n"
    "\n"
    "CONTEXTE MARQUE :\n"
    "BRAND_CONTEXT_PLACEHOLDER\n"
    "\n"
    "CONTEXTE MARCHE :\n"
    "MARKET_CONTEXT_PLACEHOLDER\n"
    "\n"
    "TYPE DE PAGE DETECTE :\n"
    "PAGE_TYPE_PLACEHOLDER\n"
    "\n"
    "METHODOLOGIE DE REFERENCE :\n"
    "METHODOLOGY_PLACEHOLDER\n"
    "\n"
    "SCORING STRICT - note uniquement ce qui est PRESENT sur la page :\n"
    "HOOK /5 : 5=hook visceral+specifique+tension | 4=hook clair sans tension | 3=generique | 2=confus | 1=pas de hook | 0=aucun\n"
    "OFFER /5 : 5=stack+prix ancre+garantie near CTA+urgence | 4=offre claire sans stack | 3=offre basique | 2=confuse | 1=incomprehensible | 0=aucune\n"
    "TRUST /5 (adapte selon contexte marque ci-dessus) :\n"
    "  - Marque etablie : 5=notoriete forte+preuves visibles | 4=notoriete reconnue OU preuves solides | 3=marque connue sans proof page | 2=peu de preuve + marque peu connue | 1=rien | 0=rien\n"
    "  - Nouveau lancement : 5=50+ reviews+photos+garantie near CTA | 4=reviews sans photos | 3=reviews generiques | 2=peu de proof | 1=aucune review | 0=rien\n"
    "FRICTION /5 : 5=zero friction+CTA repete+message coherent | 4=legere friction | 3=friction moderee | 2=friction forte | 1=mismatch evident | 0=impossible\n"
    "\n"
    "DECISION : 0-9=Do NOT launch+High | 10-14=Test small budget+Moderate | 15-20=Ready to scale+Low\n"
    "\n"
    "EXEMPLES DE CALIBRAGE (few-shots) :\n"
    "Hook 5/5 : 'Perdez 5kg en 30 jours sans regime ou on vous rembourse' → specifique, timeframe, garantie, tension\n"
    "Hook 3/5 : 'Decouvrez notre programme minceur' → generique, pas de specifique, pas de tension\n"
    "Hook 1/5 : 'Bienvenue sur notre site' → aucun hook\n"
    "Offer 5/5 : Prix 97€ barre 197€ + 3 bonus chiffres + garantie 30j visible sous CTA + 'Il reste 7 places'\n"
    "Offer 3/5 : Prix visible, livraison mentionnee, pas de garantie claire, pas d'urgence\n"
    "Trust 5/5 (nouveau) : 847 avis + photos clients + 4.8/5 + temoignages avec resultats chiffres sous CTA\n"
    "Trust 4/5 (etablie) : Gymshark / Nike = notoriete forte, meme sans reviews explicites sur la page\n"
    "Friction 5/5 : 1 seul CTA, repete 3x, pas de menu, checkout en 2 clics, message coherent pub→page\n"
    "Friction 2/5 : Menu nav complet, plusieurs CTAs concurrents, page longue sans repetition du CTA\n"
    "\n"
    "IMPORTANT : Cite des elements REELS et PRECIS du contenu analyse. Ne jamais laisser de valeurs generiques.\n"
    "\n"
    "Pour chaque action dans fix_plan, tu DOIS fournir :\n"
    "- 'how_exactly' : les instructions concretes etape par etape (pas juste 'ajouter des avis' mais 'Ajouter un bloc screenshots de 6 avis clients avec prenom + resultat specifique, place directement sous le CTA')\n"
    "- 'time_estimate' : estimation realiste du temps d'implementation\n"
    "- Classifie chaque action : 'quick_win' (moins d'1h) ou 'long_term' (plus d'1h)\n"
    "\n"
    "Retourne UNIQUEMENT ce JSON valide, rien d'autre :\n"
    "{\n"
    '  "lrs": {"mode":"X","platform":"X","offer_type":"X","brand_type":"X","page_type":"X","score_breakdown_5":{"hook":0,"offer":0,"trust":0,"friction_message_match":0}},\n'
    '  "message_match": {"status":"N/A","score_explication":"X","mismatches":[],"fix":[]},\n'
    '  "why_this_score": {"hook_detail":"X","offer_detail":"X","trust_detail":"X","friction_detail":"X","top_3_reasons":["X","X","X"],"critical_gaps":["X"]},\n'
    '  "fix_plan": {\n'
    '    "top_priority_action": {"what":"X","how_exactly":"X","time_estimate":"X","expected_impact":"X"},\n'
    '    "quick_wins": [{"what":"X","how_exactly":"X","time_estimate":"<1h","expected_impact":"X"}],\n'
    '    "long_term": [{"what":"X","how_exactly":"X","time_estimate":"X","expected_impact":"X"}],\n'
    '    "priority_actions":[{"impact":"high","effort":"low","what":"X","how":"X","how_exactly":"X","why":"X","time_estimate":"X","category":"quick_win"}],\n'
    '    "ab_tests":[{"hypothesis":"X","variant_a":"X","variant_b":"X","success_metric":"X"}]\n'
    '  },\n'
    '  "rewrite": {"headline":"X","subheadline":"X","hero_bullets":["X","X","X"],"cta_primary":"X","cta_secondary":"X","proof_block":"X","offer_stack":["X","X"],"guarantee":"X","faq_objections":["X","X"]},\n'
    '  "ads": {"angles":[{"angle":"X","rationale":"X"}],"hooks":[{"hook":"X","platform":"Meta","type":"question"}],"variants":[{"platform":"Meta","primary_text":"X","headline":"X","cta":"X"}],"script_ugc_20s":"X"}\n'
    "}"
)

# ── APPEL OPENAI ─────────────────────────────────────────────
def get_api_key():
    # 1. Variables d'environnement (.env local)
    key = os.getenv("OPENAI_API_KEY", "")
    if key and key.startswith("sk-"):
        return key
    # 2. Streamlit secrets (Streamlit Cloud)
    try:
        key = st.secrets.get("OPENAI_API_KEY", "")
        if key and key.startswith("sk-"):
            return key
    except Exception:
        pass
    return ""

def build_methodology_context(mode, offer_type):
    """Charge et tronque les fichiers methodology selon le mode."""
    parts = []

    if offer_type == "Digital product":
        m = load_txt("methodology_digital.txt")
    else:
        m = load_txt("methodology_ecom.txt")
    if m:
        parts.append("=== METHODOLOGIE SCORING ===\n" + m[:3000])

    if mode in ("Funnel Only", "Full Risk"):
        cf = load_txt("concepts_funnels.txt")
        if cf:
            parts.append("=== CONCEPTS FUNNEL ===\n" + cf[:2000])

    if mode in ("Ads Only", "Full Risk"):
        ca = load_txt("concepts_ads_meta_tiktok_google.txt")
        if ca:
            parts.append("=== CONCEPTS ADS ===\n" + ca[:2000])

    return "\n\n".join(parts)

def run_audit(mode, platform, offer_type, landing_content, ad_text, market_context, model,
              brand_type="Nouveau lancement", page_type="Non determine", page_lang="fr"):
    if OpenAI is None:
        raise ValueError("Librairie openai non installee. Relancez : pip install openai")

    api_key = get_api_key()
    if not api_key:
        raise ValueError(
            "Cle API OpenAI manquante. "
            "Ajoutez OPENAI_API_KEY dans votre fichier .env (local) "
            "ou dans Streamlit Cloud > App settings > Secrets."
        )

    client = OpenAI(api_key=api_key)

    # Charger la methodologie
    methodology_context = build_methodology_context(mode, offer_type)

    # Construire le contexte marque (Bug 1)
    if brand_type == "Marque etablie":
        brand_context = (
            "TYPE : Marque etablie (notoriete existante, historique client, presence reseaux sociaux).\n"
            "INSTRUCTION SCORING TRUST : Cette marque possede une notoriete qui ne s'affiche pas toujours "
            "sur la page. Prends en compte la reputation de marque dans le score Trust. Une marque etablie "
            "avec peu de preuves explicites sur la page peut quand meme scorer 3/5 si le contexte marque "
            "est clair. Ne pas penaliser la trust uniquement sur l'absence de reviews si c'est une marque connue.\n"
            "INSTRUCTION HOOK/OFFER : Les marques etablies peuvent avoir des hooks moins agressifs car "
            "leur notoriete porte une partie du message. Evalue le hook dans ce contexte."
        )
    else:
        brand_context = (
            "TYPE : Nouveau lancement (pas de notoriete etablie, cold traffic pur).\n"
            "INSTRUCTION SCORING TRUST : Scoring strict — un nouveau lancement doit prouver sa valeur "
            "uniquement via les elements visibles sur la page (reviews, photos, garantie, nombre d'acheteurs). "
            "Aucune notoriete implicite a prendre en compte.\n"
            "INSTRUCTION HOOK/OFFER : Sois exigeant — un nouveau lancement doit compenser l'absence de "
            "notoriete par un hook et une offre exceptionnels."
        )

    # Adapter les instructions de scoring selon le type de page détecté (Bug 2 amélioré)
    page_type_lower = page_type.lower()
    if "produit ecom" in page_type_lower or "fiche produit" in page_type_lower:
        page_type_instructions = (
            "ADAPTATION SCORING PAGE PRODUIT ECOM :\n"
            "Cette page est une fiche produit standard (pas une landing page optimisée paid traffic).\n"
            "- HOOK : Évalue le titre produit + tagline. Une page produit n'a pas de hook copywriting — "
            "note 3/5 si le titre est clair et descriptif, 2/5 si très générique.\n"
            "- FRICTION : La présence d'un menu navigation est normale sur une page produit, ne pas sur-pénaliser. "
            "Évalue la clarté du parcours d'achat (bouton add to cart visible, options claires).\n"
            "- Dans tes recommandations, propose des améliorations réalistes POUR UNE PAGE PRODUIT "
            "(pas 'supprimer la navigation' mais 'améliorer les photos', 'renforcer les avis', etc.)."
        )
    elif "catalogue" in page_type_lower:
        page_type_instructions = (
            "ADAPTATION SCORING CATALOGUE ECOM :\n"
            "Cette page liste plusieurs produits — ce n'est PAS une landing page de conversion directe.\n"
            "- HOOK 1-2/5 est normal (pas de promesse unique sur un catalogue).\n"
            "- FRICTION modérée est normale (navigation = fonctionnelle sur un catalogue).\n"
            "- Dans tes recommandations, indique clairement que pour améliorer les conversions paid traffic, "
            "l'idéal est de créer une landing page dédiée plutôt que d'envoyer sur le catalogue."
        )
    elif "homepage" in page_type_lower or "accueil" in page_type_lower:
        page_type_instructions = (
            "ADAPTATION SCORING HOMEPAGE :\n"
            "Cette page est une page d'accueil généraliste — pas optimisée pour la conversion paid traffic.\n"
            "- Scores bas sur Hook et Friction sont normaux et attendus.\n"
            "- Dans tes recommandations, INSISTE sur la nécessité de créer une landing page dédiée "
            "pour les campagnes paid traffic au lieu d'envoyer sur la homepage."
        )
    elif "saas" in page_type_lower or "logiciel" in page_type_lower:
        page_type_instructions = (
            "ADAPTATION SCORING PAGE SAAS :\n"
            "Cette page est une page SaaS/logiciel. Critères adaptés :\n"
            "- HOOK : évalue la clarté de la proposition de valeur (ce que fait le logiciel + pour qui + résultat).\n"
            "- OFFER : évalue la clarté du pricing, la présence d'un free trial ou démo.\n"
            "- TRUST : logos clients, témoignages, nombre d'utilisateurs, certifications.\n"
            "- FRICTION : formulaire d'inscription simple, CTA clair (Start free trial / Book a demo)."
        )
    elif "lead gen" in page_type_lower:
        page_type_instructions = (
            "ADAPTATION SCORING LEAD GEN :\n"
            "Cette page capture des leads (email, inscription). Critères adaptés :\n"
            "- OFFER : évalue la valeur perçue du lead magnet (gratuit, mais doit sembler précieux).\n"
            "- FRICTION : formulaire simple (1 seul champ email = 5/5, formulaire long = 1/5).\n"
            "- TRUST : témoignages de personnes ayant bénéficié du contenu gratuit."
        )
    elif "blog" in page_type_lower or "article" in page_type_lower:
        page_type_instructions = (
            "ADAPTATION SCORING BLOG/ARTICLE :\n"
            "Cette page est un article de blog — pas une page de conversion directe.\n"
            "- Les scores Hook/Offer/Trust/Friction doivent être interprétés dans le contexte éditorial.\n"
            "- Dans tes recommandations, propose comment améliorer les CTAs dans l'article "
            "pour capturer des leads ou diriger vers une offre."
        )
    else:
        page_type_instructions = (
            "Applique le scoring standard landing page de conversion paid traffic."
        )

    # Instruction langue (détection automatique)
    if page_lang == "en":
        lang_instruction = (
            "LANGUE DE LA PAGE : Anglais.\n"
            "La page analysée est en anglais. Analyse les éléments en anglais tel quels (hook, CTA, etc.) "
            "et cite-les dans leur langue originale dans les détails. Tes réponses JSON restent en français."
        )
    elif page_lang == "mixte":
        lang_instruction = (
            "LANGUE DE LA PAGE : Mixte (français + anglais).\n"
            "Cite les éléments dans leur langue originale. Tes réponses JSON restent en français."
        )
    else:
        lang_instruction = "LANGUE DE LA PAGE : Français."

    system = (
        SYSTEM_PROMPT_BASE
        .replace("BRAND_CONTEXT_PLACEHOLDER", brand_context)
        .replace("MARKET_CONTEXT_PLACEHOLDER", market_context)
        .replace("PAGE_TYPE_PLACEHOLDER", page_type + "\n\n" + page_type_instructions + "\n\n" + lang_instruction)
        .replace("METHODOLOGY_PLACEHOLDER", methodology_context or "Non disponible.")
    )

    # Construire le prompt utilisateur
    user_parts = [
        "AUDIT LRS -- " + mode.upper(),
        "Plateforme : " + platform + " | Offre : " + offer_type + " | Marque : " + brand_type,
        "Type de page detecte : " + page_type + " | Langue : " + page_lang,
        "",
    ]

    if mode == "Funnel Only" and landing_content:
        user_parts += [
            "CONTENU LANDING PAGE :",
            landing_content,
            "",
            "INSTRUCTIONS : Audite cette landing page. friction_message_match = friction interne uniquement. message_match.status = N/A.",
            "Cite des elements PRECIS et REELS de la page dans hook_detail, offer_detail, trust_detail, friction_detail.",
            "Dans ads, propose des pubs qui matcheraient cette page.",
        ]
    elif mode == "Ads Only" and ad_text:
        user_parts += [
            "PUBLICITE A AUDITER :",
            ad_text,
            "",
            "INSTRUCTIONS : Audite cette pub. friction_message_match = coherence interne. message_match.status = N/A.",
            "Cite des elements PRECIS de la pub dans les details.",
        ]
    elif mode == "Full Risk":
        if landing_content:
            user_parts += ["CONTENU LANDING PAGE :", landing_content, ""]
        if ad_text:
            user_parts += ["PUBLICITE :", ad_text, ""]
        user_parts += [
            "INSTRUCTIONS : Audit COMPLET. friction_message_match = coherence pub+landing.",
            "message_match : cite le texte EXACT de la pub ET de la landing pour chaque mismatch.",
            "Pour chaque fix, donne un exemple de texte exact a ecrire.",
        ]

    user_parts += ["", "RAPPEL : JSON uniquement. Francais. Sois PRECIS -- cite le contenu analyse."]
    user_prompt = "\n".join(user_parts)

    # Retry automatique : 3 tentatives avec backoff
    response = None
    last_err = None
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user_prompt},
                ],
                temperature=0.15,
                max_tokens=4500,
                response_format={"type": "json_object"},
            )
            break  # Succès
        except Exception as e:
            last_err = str(e)
            if "api_key" in last_err.lower() or "authentication" in last_err.lower():
                raise ValueError("Cle API invalide ou expiree. Verifiez votre OPENAI_API_KEY.")
            if "quota" in last_err.lower() or "billing" in last_err.lower():
                raise ValueError("Quota OpenAI epuise. Verifiez votre solde sur platform.openai.com.")
            if attempt < 2:
                wait = 2 ** attempt  # 1s, 2s
                time.sleep(wait)
            else:
                # 3ème échec
                if "rate_limit" in last_err.lower():
                    raise ValueError("Rate limit OpenAI atteint apres 3 tentatives. Attendez et relancez.")
                raise ValueError("Erreur OpenAI apres 3 tentatives : " + last_err)

    if response is None:
        raise ValueError("Erreur OpenAI : pas de reponse apres 3 tentatives.")

    raw = response.choices[0].message.content or ""

    # Nettoyage JSON robuste (securite supplementaire)
    clean = raw.strip()
    for m2 in ["```json", "```"]:
        clean = clean.replace(m2, "")
    clean = clean.strip()

    if clean and clean[0] == '"':
        clean = "{" + clean
    if clean and not clean.rstrip().endswith("}"):
        clean = clean.rstrip() + "}"

    s, e2 = clean.find("{"), clean.rfind("}") + 1
    if s != -1 and e2 > s:
        clean = clean[s:e2]

    result = None
    for attempt in [clean, clean + "}", clean + "}}"]:
        try:
            result = json.loads(attempt)
            break
        except json.JSONDecodeError:
            continue

    if result is None:
        result = {
            "lrs": {"mode": mode, "platform": platform, "offer_type": offer_type,
                    "score_breakdown_5": {"hook": 0, "offer": 0, "trust": 0, "friction_message_match": 0}},
            "message_match": {"status": "N/A", "score_explication": "Analyse incomplete - relance l'audit", "mismatches": [], "fix": []},
            "why_this_score": {
                "hook_detail": "Analyse incomplete - relance l'audit",
                "offer_detail": "Analyse incomplete - relance l'audit",
                "trust_detail": "Analyse incomplete - relance l'audit",
                "friction_detail": "Analyse incomplete - relance l'audit",
                "top_3_reasons": ["Analyse incomplete", "Relance l'audit", "Si erreur persiste, reduis le contenu"],
                "critical_gaps": ["Analyse incomplete"]
            },
            "fix_plan": {"priority_actions": [], "ab_tests": []},
            "rewrite": {"headline": "", "subheadline": "", "hero_bullets": [], "cta_primary": "",
                        "cta_secondary": "", "proof_block": "", "offer_stack": [], "guarantee": "", "faq_objections": []},
            "ads": {"angles": [], "hooks": [], "variants": [], "script_ugc_20s": ""}
        }
        st.warning("Le modele n'a pas retourne un JSON valide. Relance l'audit ou reduis le contenu.")

    # Calculs cote code
    bd       = result.get("lrs", {}).get("score_breakdown_5", {})
    hook     = max(0, min(5, int(bd.get("hook", 0))))
    offer    = max(0, min(5, int(bd.get("offer", 0))))
    trust    = max(0, min(5, int(bd.get("trust", 0))))
    friction = max(0, min(5, int(bd.get("friction_message_match", 0))))
    score    = hook + offer + trust + friction

    decision, risk = get_decision(score)
    tier            = get_tier(score)
    bench           = CVR_BENCHMARKS.get(offer_type, CVR_BENCHMARKS["Digital product"])
    cvr_cur, cvr_fix, cvr_up = bench[tier]

    result["_c"] = {
        "score": score, "hook": hook, "offer": offer, "trust": trust, "friction": friction,
        "decision": decision, "risk": risk,
        "cvr_cur": cvr_cur, "cvr_fix": cvr_fix, "cvr_up": cvr_up,
    }
    return result


# ── HELPERS : parse JSON + compute scores (partagés par run_audit et run_audit_stream) ──
def _parse_audit_json(raw_text, mode, platform, offer_type):
    """Parse le JSON brut retourné par le LLM et compute les scores."""
    clean = raw_text.strip()
    for m2 in ["```json", "```"]:
        clean = clean.replace(m2, "")
    clean = clean.strip()
    if clean and clean[0] == '"':
        clean = "{" + clean
    if clean and not clean.rstrip().endswith("}"):
        clean = clean.rstrip() + "}"
    s, e2 = clean.find("{"), clean.rfind("}") + 1
    if s != -1 and e2 > s:
        clean = clean[s:e2]

    result = None
    for attempt in [clean, clean + "}", clean + "}}"]:
        try:
            result = json.loads(attempt)
            break
        except json.JSONDecodeError:
            continue

    if result is None:
        result = {
            "lrs": {"mode": mode, "platform": platform, "offer_type": offer_type,
                    "score_breakdown_5": {"hook": 0, "offer": 0, "trust": 0, "friction_message_match": 0}},
            "message_match": {"status": "N/A", "score_explication": "Analyse incomplete", "mismatches": [], "fix": []},
            "why_this_score": {"hook_detail": "Analyse incomplete", "offer_detail": "Analyse incomplete",
                               "trust_detail": "Analyse incomplete", "friction_detail": "Analyse incomplete",
                               "top_3_reasons": ["Analyse incomplete"], "critical_gaps": []},
            "fix_plan": {"priority_actions": [], "ab_tests": []},
            "rewrite": {"headline": "", "subheadline": "", "hero_bullets": [], "cta_primary": "",
                        "cta_secondary": "", "proof_block": "", "offer_stack": [], "guarantee": "", "faq_objections": []},
            "ads": {"angles": [], "hooks": [], "variants": [], "script_ugc_20s": ""},
        }

    bd       = result.get("lrs", {}).get("score_breakdown_5", {})
    hook     = max(0, min(5, int(bd.get("hook", 0))))
    offer    = max(0, min(5, int(bd.get("offer", 0))))
    trust    = max(0, min(5, int(bd.get("trust", 0))))
    friction = max(0, min(5, int(bd.get("friction_message_match", 0))))
    score    = hook + offer + trust + friction
    decision, risk = get_decision(score)
    tier     = get_tier(score)
    bench    = CVR_BENCHMARKS.get(offer_type, CVR_BENCHMARKS["Digital product"])
    cvr_cur, cvr_fix, cvr_up = bench[tier]
    result["_c"] = {
        "score": score, "hook": hook, "offer": offer, "trust": trust, "friction": friction,
        "decision": decision, "risk": risk,
        "cvr_cur": cvr_cur, "cvr_fix": cvr_fix, "cvr_up": cvr_up,
    }
    return result


# ── STREAMING AUDIT ───────────────────────────────────────────
STREAM_STAGES = [
    (0,    "📡 Connexion au modèle IA..."),
    (250,  "🔍 Lecture des patterns de conversion..."),
    (800,  "📊 Scoring Hook · Offer · Trust · Friction..."),
    (1800, "🎯 Génération du plan d'action prioritaire..."),
    (3000, "✍️  Rédaction rewrites & angles pub..."),
]

def run_audit_stream(mode, platform, offer_type, landing_content, ad_text, market_context, model,
                     brand_type="Nouveau lancement", page_type="Non determine", page_lang="fr",
                     status_stage=None, status_tokens=None):
    """
    Identique à run_audit() mais utilise stream=True pour afficher la progression
    en temps réel dans le status Streamlit.
    status_stage  : st.empty() pour afficher l'étape courante
    status_tokens : st.empty() pour afficher le compteur de tokens
    """
    if OpenAI is None:
        raise ValueError("Librairie openai non installee.")
    api_key = get_api_key()
    if not api_key:
        raise ValueError("Cle API OpenAI manquante. Ajoutez OPENAI_API_KEY dans .env ou Streamlit Secrets.")

    client = OpenAI(api_key=api_key)
    methodology_context = build_methodology_context(mode, offer_type)

    # ── Brand context ──
    if brand_type == "Marque etablie":
        brand_context = (
            "TYPE : Marque etablie (notoriete existante).\n"
            "INSTRUCTION SCORING TRUST : prend en compte la reputation de marque. "
            "Ne pas penaliser trust uniquement sur absence de reviews si marque connue.\n"
            "INSTRUCTION HOOK/OFFER : marques etablies peuvent avoir hooks moins agressifs."
        )
    else:
        brand_context = (
            "TYPE : Nouveau lancement (cold traffic pur).\n"
            "INSTRUCTION SCORING TRUST : Scoring strict — prouver valeur uniquement via elements visibles.\n"
            "INSTRUCTION HOOK/OFFER : Sois exigeant — doit compenser absence de notoriete."
        )

    # ── Page type instructions ──
    pt_lower = page_type.lower()
    if "produit ecom" in pt_lower or "fiche produit" in pt_lower:
        page_type_instructions = ("ADAPTATION SCORING PAGE PRODUIT ECOM : note 3/5 si titre clair, "
                                   "ne pas sur-penaliser navigation. Propose améliorations réalistes pour page produit.")
    elif "catalogue" in pt_lower:
        page_type_instructions = ("ADAPTATION SCORING CATALOGUE : HOOK 1-2/5 normal, FRICTION moderee normale. "
                                   "Recommande landing page dédiée pour paid traffic.")
    elif "homepage" in pt_lower or "accueil" in pt_lower:
        page_type_instructions = ("ADAPTATION SCORING HOMEPAGE : scores bas Hook/Friction normaux. "
                                   "INSISTE sur nécessité landing page dédiée pour paid traffic.")
    elif "saas" in pt_lower or "logiciel" in pt_lower:
        page_type_instructions = ("ADAPTATION SCORING SAAS : HOOK = clarté proposition valeur, "
                                   "OFFER = pricing/free trial, TRUST = logos/témoignages, FRICTION = form simple.")
    elif "lead gen" in pt_lower:
        page_type_instructions = ("ADAPTATION SCORING LEAD GEN : OFFER = valeur perçue lead magnet, "
                                   "FRICTION = formulaire simple (1 champ = 5/5).")
    elif "blog" in pt_lower or "article" in pt_lower:
        page_type_instructions = ("ADAPTATION SCORING BLOG : interprete scores dans contexte éditorial. "
                                   "Propose amélioration CTAs article.")
    else:
        page_type_instructions = "Applique le scoring standard landing page de conversion paid traffic."

    if page_lang == "en":
        lang_instruction = "LANGUE : Anglais. Cite éléments en anglais, réponses JSON en français."
    elif page_lang == "mixte":
        lang_instruction = "LANGUE : Mixte FR+EN. Cite dans langue originale, JSON en français."
    else:
        lang_instruction = "LANGUE DE LA PAGE : Français."

    system = (
        SYSTEM_PROMPT_BASE
        .replace("BRAND_CONTEXT_PLACEHOLDER", brand_context)
        .replace("MARKET_CONTEXT_PLACEHOLDER", market_context)
        .replace("PAGE_TYPE_PLACEHOLDER", page_type + "\n\n" + page_type_instructions + "\n\n" + lang_instruction)
        .replace("METHODOLOGY_PLACEHOLDER", methodology_context or "Non disponible.")
    )

    user_parts = [
        "AUDIT LRS -- " + mode.upper(),
        "Plateforme : " + platform + " | Offre : " + offer_type + " | Marque : " + brand_type,
        "Type de page detecte : " + page_type + " | Langue : " + page_lang, "",
    ]
    if mode == "Funnel Only" and landing_content:
        user_parts += ["CONTENU LANDING PAGE :", landing_content, "",
                       "INSTRUCTIONS : Audite cette landing page. friction_message_match = friction interne. "
                       "message_match.status = N/A. Cite elements PRECIS."]
    elif mode == "Ads Only" and ad_text:
        user_parts += ["PUBLICITE A AUDITER :", ad_text, "",
                       "INSTRUCTIONS : Audite cette pub. friction_message_match = coherence interne. "
                       "message_match.status = N/A. Cite elements PRECIS."]
    elif mode == "Full Risk":
        if landing_content:
            user_parts += ["CONTENU LANDING PAGE :", landing_content, ""]
        if ad_text:
            user_parts += ["PUBLICITE :", ad_text, ""]
        user_parts += ["INSTRUCTIONS : Audit COMPLET. friction_message_match = coherence pub+landing. "
                       "message_match : cite texte EXACT. Pour chaque fix, donne exemple exact."]
    user_parts += ["", "RAPPEL : JSON uniquement. Francais. Sois PRECIS."]
    user_prompt = "\n".join(user_parts)

    # ── Streaming call ──
    def _update_stage(n_chars):
        if status_stage is None:
            return
        for i, (threshold, msg) in reversed(list(enumerate(STREAM_STAGES))):
            if n_chars >= threshold:
                status_stage.markdown(
                    f"<div style='padding:8px 12px;background:#1a1a2e;border-radius:6px;"
                    f"border-left:3px solid #6366f1;color:#ccc;font-size:0.88em'>{msg}</div>",
                    unsafe_allow_html=True
                )
                break

    full_text = ""
    last_err = None
    _update_stage(0)

    for attempt in range(3):
        try:
            stream = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user_prompt},
                ],
                temperature=0.15,
                max_tokens=4500,
                response_format={"type": "json_object"},
                stream=True,
            )
            full_text = ""
            prev_stage = -1
            for chunk in stream:
                delta = (chunk.choices[0].delta.content or "") if chunk.choices else ""
                full_text += delta
                n = len(full_text)
                # Update stage when crossing a threshold
                cur_stage = sum(1 for t, _ in STREAM_STAGES if n >= t) - 1
                if cur_stage > prev_stage:
                    prev_stage = cur_stage
                    _update_stage(n)
                # Update token counter every ~200 chars
                if status_tokens and n % 200 < len(delta) + 1:
                    status_tokens.caption(f"⏳ {n} caractères reçus...")
            break  # success
        except Exception as e:
            last_err = str(e)
            if "api_key" in last_err.lower() or "authentication" in last_err.lower():
                raise ValueError("Cle API invalide ou expiree.")
            if "quota" in last_err.lower() or "billing" in last_err.lower():
                raise ValueError("Quota OpenAI epuise. Verifiez votre solde sur platform.openai.com.")
            if attempt < 2:
                time.sleep(2 ** attempt)
            else:
                if "rate_limit" in last_err.lower():
                    raise ValueError("Rate limit OpenAI apres 3 tentatives. Attendez et relancez.")
                raise ValueError("Erreur OpenAI apres 3 tentatives : " + last_err)

    if status_tokens:
        status_tokens.caption(f"✅ {len(full_text)} caractères — parsing JSON...")

    return _parse_audit_json(full_text, mode, platform, offer_type)


# ── EXPORT TXT ───────────────────────────────────────────────
def export_txt(result, meta):
    c   = result.get("_c", {})
    why = result.get("why_this_score", {})
    mm  = result.get("message_match", {})
    fp  = result.get("fix_plan", {})
    rw  = result.get("rewrite", {})
    ads = result.get("ads", {})

    lrs_meta = result.get("lrs", {})
    L = ["=" * 60,
         "LRS - LAUNCH RISK SYSTEM V" + APP_VERSION,
         "Audit du " + meta.get("timestamp", ""),
         "=" * 60, "",
         "MODE         : " + meta.get("mode", ""),
         "PLATEFORME   : " + meta.get("platform", ""),
         "TYPE D'OFFRE : " + meta.get("offer_type", ""),
         "TYPE MARQUE  : " + lrs_meta.get("brand_type", meta.get("brand_type", "N/A")),
         "TYPE PAGE    : " + lrs_meta.get("page_type", meta.get("page_type", "N/A")),
         "URL          : " + meta.get("url", "N/A"),
         "", "-" * 40, "SCORE", "-" * 40,
         "Total   : " + str(c.get("score", 0)) + " / 20",
         "Risk    : " + c.get("risk", ""),
         "Decision: " + c.get("decision", ""),
         "",
         "  Hook     : " + str(c.get("hook", 0)) + "/5",
         "  Offer    : " + str(c.get("offer", 0)) + "/5",
         "  Trust    : " + str(c.get("trust", 0)) + "/5",
         "  Friction : " + str(c.get("friction", 0)) + "/5",
         "", "-" * 40, "CVR", "-" * 40,
         "Actuel   : " + c.get("cvr_cur", ""),
         "Post-fix : " + c.get("cvr_fix", ""),
         "Uplift   : " + c.get("cvr_up", ""),
         "", "-" * 40, "ANALYSE", "-" * 40,
         "Hook     : " + why.get("hook_detail", ""),
         "",
         "Offer    : " + why.get("offer_detail", ""),
         "",
         "Trust    : " + why.get("trust_detail", ""),
         "",
         "Friction : " + why.get("friction_detail", ""),
         "", "Top 3 raisons :"]

    for i, r in enumerate(why.get("top_3_reasons", []), 1):
        L.append("  " + str(i) + ". " + r)

    L += ["", "Critical Gaps :"]
    for g in why.get("critical_gaps", []):
        L.append("  - " + g)

    ms = mm.get("status", "N/A")
    if ms not in ("N/A", None, ""):
        L += ["", "-" * 40, "MESSAGE MATCH", "-" * 40,
              "Statut : " + ms, mm.get("score_explication", ""), "", "Mismatches :"]
        for m2 in mm.get("mismatches", []):
            L.append("  - " + m2)
        L += ["", "Corrections :"]
        for f in mm.get("fix", []):
            L.append("  -> " + f)

    L += ["", "-" * 40, "PLAN D'ACTION", "-" * 40]

    top_prio = fp.get("top_priority_action", {})
    if top_prio and top_prio.get("what"):
        L += [">>> ACTION PRIORITAIRE #1 <<<",
              "  Quoi         : " + top_prio.get("what", ""),
              "  Comment exact : " + top_prio.get("how_exactly", ""),
              "  Impact attendu: " + top_prio.get("expected_impact", ""),
              "  Temps estime  : " + top_prio.get("time_estimate", ""), ""]

    quick_wins = fp.get("quick_wins", [])
    if quick_wins:
        L += ["--- QUICK WINS (moins d'1h) ---"]
        for qw in quick_wins:
            L += ["[QUICK WIN] " + qw.get("what", ""),
                  "  Comment : " + qw.get("how_exactly", ""),
                  "  Impact  : " + qw.get("expected_impact", ""),
                  "  Temps   : " + qw.get("time_estimate", "<1h"), ""]

    long_term = fp.get("long_term", [])
    if long_term:
        L += ["--- AMELIORATIONS LONG TERME ---"]
        for lt in long_term:
            L += ["[LONG TERME] " + lt.get("what", ""),
                  "  Comment : " + lt.get("how_exactly", ""),
                  "  Impact  : " + lt.get("expected_impact", ""),
                  "  Temps   : " + lt.get("time_estimate", ""), ""]

    for a in fp.get("priority_actions", []):
        L += ["[" + a.get("impact", "").upper() + " | " + a.get("effort", "").upper() + "]",
              "  Quoi    : " + a.get("what", ""),
              "  Comment : " + a.get("how_exactly", a.get("how", "")),
              "  Pourquoi: " + a.get("why", ""),
              "  Temps   : " + a.get("time_estimate", ""), ""]

    L += ["-" * 40, "REWRITE", "-" * 40]
    if rw.get("headline"):    L.append("Headline : " + rw["headline"])
    if rw.get("subheadline"): L.append("Sub      : " + rw["subheadline"])
    L += ["", "Bullets :"]
    for b in rw.get("hero_bullets", []): L.append("  - " + b)
    if rw.get("cta_primary"):  L.append("\nCTA : " + rw["cta_primary"])
    if rw.get("guarantee"):    L.append("Garantie : " + rw["guarantee"])

    L += ["", "Offer Stack :"]
    for o in rw.get("offer_stack", []): L.append("  - " + o)

    L += ["", "-" * 40, "ADS", "-" * 40, "Hooks :"]
    for h in ads.get("hooks", []):
        if isinstance(h, dict):
            L.append("  [" + h.get("platform", "") + "/" + h.get("type", "") + "] " + h.get("hook", ""))
        else:
            L.append("  " + str(h))

    for i, v in enumerate(ads.get("variants", []), 1):
        L += ["", "Variante " + str(i) + " -- " + v.get("platform", ""),
              "  Headline : " + v.get("headline", ""),
              "  Text     : " + v.get("primary_text", ""),
              "  CTA      : " + v.get("cta", "")]

    if ads.get("script_ugc_20s"):
        L += ["", "Script UGC :", ads["script_ugc_20s"]]

    L += ["", "=" * 60, "LRS V" + APP_VERSION, "=" * 60]
    return "\n".join(L)


# ── EMAIL NOTIFICATIONS ──────────────────────────────────────
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders as email_encoders

def _get_smtp_config():
    """Lit la config SMTP depuis les secrets Streamlit ou les variables d'env."""
    try:
        cfg = st.secrets.get("smtp", {})
        host     = cfg.get("host",     os.getenv("SMTP_HOST", ""))
        port     = int(cfg.get("port", os.getenv("SMTP_PORT", 587)))
        user     = cfg.get("user",     os.getenv("SMTP_USER", ""))
        password = cfg.get("password", os.getenv("SMTP_PASSWORD", ""))
        return host, port, user, password
    except Exception:
        return (os.getenv("SMTP_HOST",""), int(os.getenv("SMTP_PORT",587)),
                os.getenv("SMTP_USER",""), os.getenv("SMTP_PASSWORD",""))

def send_audit_email(result, meta, to_email, pdf_bytes=None):
    """
    Envoie le résumé de l'audit par email.
    Configure SMTP dans Streamlit Secrets : [smtp] host/port/user/password
    ou dans les variables d'environnement SMTP_HOST/PORT/USER/PASSWORD.
    """
    host, port, user, password = _get_smtp_config()
    if not host or not user:
        raise ValueError(
            "SMTP non configuré. Ajoutez [smtp] host/port/user/password dans "
            "Streamlit Secrets ou SMTP_HOST/PORT/USER/PASSWORD dans .env"
        )

    c   = result.get("_c", {})
    score    = c.get("score", 0)
    decision = c.get("decision", "")
    url      = meta.get("url", meta.get("offer_type", ""))
    ts       = meta.get("timestamp", "")
    mode_m   = meta.get("mode", "")

    score_color = "#FF4444" if score <= 9 else "#FF8C00" if score <= 14 else "#22c55e"

    fp  = result.get("fix_plan", {})
    top = fp.get("top_priority_action", {})
    qws = fp.get("quick_wins", [])[:3]

    qws_html = "".join(
        f"<li style='margin:4px 0;color:#555'>{qw.get('what','')}</li>"
        for qw in qws
    )

    html_body = f"""
<!DOCTYPE html>
<html><body style='font-family:Inter,-apple-system,sans-serif;background:#f4f4f8;padding:24px'>
<div style='max-width:600px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;
            box-shadow:0 2px 12px rgba(0,0,0,0.08)'>

  <div style='background:linear-gradient(135deg,#6366f1,#4f46e5);padding:24px 28px'>
    <div style='color:#fff;font-size:1.3rem;font-weight:800'>🚦 LRS™ — Résultat d'Audit</div>
    <div style='color:rgba(255,255,255,0.7);font-size:0.85rem;margin-top:4px'>{ts} · {mode_m}</div>
  </div>

  <div style='padding:24px 28px'>
    <div style='font-size:0.85rem;color:#888;margin-bottom:4px'>URL / Offre</div>
    <div style='font-size:0.95rem;color:#1a1a2e;margin-bottom:20px'>{url}</div>

    <div style='background:#f8f8fc;border-radius:10px;padding:20px;text-align:center;margin-bottom:20px'>
      <div style='color:#888;font-size:0.75rem;text-transform:uppercase;letter-spacing:1px'>Score LRS</div>
      <div style='color:{score_color};font-size:3.5rem;font-weight:900;line-height:1'>{score}</div>
      <div style='color:#aaa;font-size:0.9rem'>/20</div>
      <div style='color:{score_color};font-size:1.1rem;font-weight:700;margin-top:8px'>{decision}</div>
    </div>

    {"<div style='margin-bottom:20px'><div style='font-weight:700;color:#1a1a2e;margin-bottom:8px'>🎯 Action Prioritaire</div><div style='background:#fff0f0;border-left:3px solid #FF4444;border-radius:6px;padding:12px 16px;color:#333'>" + top.get("what","") + "</div></div>" if top and top.get("what") else ""}

    {"<div><div style='font-weight:700;color:#1a1a2e;margin-bottom:8px'>⚡ Quick Wins</div><ul style='padding-left:18px;margin:0'>" + qws_html + "</ul></div>" if qws_html else ""}
  </div>

  <div style='background:#f4f4f8;padding:14px 28px;text-align:center'>
    <span style='color:#aaa;font-size:0.78rem'>LRS™ — Launch Risk System V{APP_VERSION}</span>
  </div>
</div>
</body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🚦 LRS Audit — Score {score}/20 — {decision} — {str(url)[:40]}"
    msg["From"]    = user
    msg["To"]      = to_email
    msg.attach(MIMEText(html_body, "html"))

    if pdf_bytes:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(pdf_bytes)
        email_encoders.encode_base64(part)
        safe_url = (url or "audit").replace("https://","").replace("http://","").replace("/","_")[:40]
        fname_pdf = f"LRS_{ts.replace('/','').replace(':','').replace(' ','_')}_{safe_url}.pdf"
        part.add_header("Content-Disposition", f"attachment; filename={fname_pdf}")
        msg.attach(part)

    with smtplib.SMTP(host, port) as server:
        server.ehlo()
        server.starttls()
        server.login(user, password)
        server.sendmail(user, to_email, msg.as_string())


def build_share_text(result, meta):
    """Génère un résumé court et lisible à copier-coller / partager."""
    c   = result.get("_c", {})
    why = result.get("why_this_score", {})
    fp  = result.get("fix_plan", {})
    score    = c.get("score", 0)
    decision = c.get("decision", "")
    url      = meta.get("url", meta.get("offer_type", "Audit"))
    ts       = meta.get("timestamp", "")
    mode_m   = meta.get("mode", "")

    top3 = why.get("top_3_reasons", [])[:3]
    top  = fp.get("top_priority_action", {})
    qws  = fp.get("quick_wins", [])[:3]

    lines = [
        "═══ 🚦 LRS™ — RÉSULTAT D'AUDIT ═══",
        f"📅 {ts}  |  {mode_m}",
        f"🔗 {url}",
        "",
        f"{'🟢' if score >= 15 else '🟡' if score >= 10 else '🔴'} Score : {score}/20 — {decision}",
        f"   Hook {c.get('hook',0)}/5  ·  Offer {c.get('offer',0)}/5  ·  Trust {c.get('trust',0)}/5  ·  Friction {c.get('friction',0)}/5",
        "",
    ]
    if top3:
        lines.append("📋 Raisons du score :")
        for r in top3:
            lines.append(f"   • {r}")
        lines.append("")
    if top and top.get("what"):
        lines.append(f"🎯 Action #1 : {top.get('what','')}")
        lines.append("")
    if qws:
        lines.append("⚡ Quick Wins :")
        for qw in qws:
            lines.append(f"   • {qw.get('what','')}")
        lines.append("")
    lines.append(f"Généré par LRS™ V{APP_VERSION} — Launch Risk System")
    return "\n".join(lines)


def render_share_widget(result, meta, key_prefix="share"):
    """Widget 'Partager' — affiche un résumé formaté copier-coller."""
    with st.expander("🔗 Partager — résumé rapide"):
        share_txt = build_share_text(result, meta)
        st.code(share_txt, language=None)
        st.caption("Sélectionnez tout (Ctrl+A) puis copiez — ou utilisez le bouton copier en haut à droite du bloc.")


def render_email_widget(result, meta, key_prefix="email"):
    """Widget compact pour envoyer le rapport par email — utilisable partout."""
    host, _, user, _ = _get_smtp_config()
    smtp_ready = bool(host and user)

    with st.expander("📧 Envoyer par email"):
        if not smtp_ready:
            st.warning(
                "SMTP non configuré. Ajoutez dans Streamlit Secrets :\n"
                "```toml\n[smtp]\nhost = \"smtp.gmail.com\"\nport = 587\n"
                "user = \"votre@email.com\"\npassword = \"votre_app_password\"\n```"
            )
            st.caption("Gmail : activez l'authentification 2FA puis créez un 'App Password' dans votre compte Google.")
        else:
            to_addr = st.text_input("Adresse email destinataire",
                                     placeholder="client@exemple.com",
                                     key=f"{key_prefix}_to")
            send_pdf = st.checkbox("Joindre le rapport PDF", value=True, key=f"{key_prefix}_pdf")
            if st.button("📤 Envoyer", key=f"{key_prefix}_send", type="primary"):
                if not to_addr or "@" not in to_addr:
                    st.error("Adresse email invalide.")
                else:
                    with st.spinner("Envoi en cours..."):
                        try:
                            pdf_b = None
                            if send_pdf and PDF_AVAILABLE:
                                pdf_b = generate_pdf_report(result, {**meta, "version": APP_VERSION})
                            send_audit_email(result, meta, to_addr, pdf_bytes=pdf_b)
                            st.success(f"✅ Email envoyé à {to_addr}")
                        except Exception as email_err:
                            st.error(f"Erreur envoi : {email_err}")


# ── CHECKLIST ────────────────────────────────────────────────
CHECKLIST = [
    ("Hook & Headline", [
        "La headline repond clairement : qu'est-ce que j'obtiens ?",
        "La headline contient un chiffre, timeframe ou persona specifique",
        "L'image hero montre le produit en action ou le resultat visible",
        "Le visiteur comprend la valeur en moins de 5 secondes",
    ]),
    ("Offre", [
        "Le prix est visible sans scroller",
        "Il y a un offer stack avec valeurs chiffrees",
        "La garantie est visible directement sous le CTA principal",
        "Il y a une urgence ou rarete credible",
    ]),
    ("Trust", [
        "Il y a au moins 10 avis ou temoignages",
        "Les temoignages ont prenom + resultat specifique",
        "Il y a un badge de paiement securise visible",
        "Le nombre total d'acheteurs est mentionne",
    ]),
    ("Friction & CTA", [
        "Il y a un seul CTA principal",
        "Le CTA est repete au moins 3 fois sur la page",
        "Pas de menu de navigation distrayant",
        "Le parcours d'achat fait moins de 3 clics",
    ]),
    ("Tracking", [
        "Le Pixel Meta ou TikTok est installe et verifie",
        "L'evenement Purchase est configure",
        "Google Analytics est actif",
        "Un test d'achat a ete effectue",
    ]),
]

def render_checklist():
    st.subheader("Checklist Pre-Lancement")
    st.caption("Cochez chaque element avant de lancer vos campagnes.")
    total, checked = sum(len(i) for _, i in CHECKLIST), 0
    for cat, items in CHECKLIST:
        st.markdown("**" + cat + "**")
        for item in items:
            if st.checkbox(item, key="chk_" + str(hash(item))):
                checked += 1
        st.markdown("")
    pct = int(checked / total * 100) if total > 0 else 0
    st.markdown("**Progression : " + str(checked) + "/" + str(total) + " (" + str(pct) + "%)**")
    st.progress(pct / 100)
    if pct < 50:   st.error("Moins de 50% -- Ne lancez pas encore.")
    elif pct < 80: st.warning("Entre 50-80% -- Testez en petit budget.")
    else:          st.success("80%+ -- Fondamentaux solides. Vous pouvez lancer.")

# ── AFFICHAGE RESULTATS ──────────────────────────────────────
RISK_COLORS  = {"High": "#FF4444", "Moderate": "#FF8C00", "Low": "#22c55e"}
MATCH_COLORS = {"Good": "#22c55e", "Moderate": "#FF8C00", "Bad": "#FF4444", "N/A": "#555"}

def bar(v, m=5):
    f = round(v / m * 10)
    return "█" * f + "░" * (10 - f)

def render_results(result):
    c   = result.get("_c", {})
    why = result.get("why_this_score", {})
    mm  = result.get("message_match", {})
    fp  = result.get("fix_plan", {})
    rw  = result.get("rewrite", {})
    ads = result.get("ads", {})

    score = c.get("score", 0)
    risk  = c.get("risk", "High")
    dec   = c.get("decision", "Do NOT launch")
    ms    = mm.get("status", "N/A")

    lrs_meta           = result.get("lrs", {})
    page_type_display  = lrs_meta.get("page_type", "")
    score_color        = RISK_COLORS.get(risk, "#888")
    dec_emoji          = "🔴" if risk == "High" else "🟡" if risk == "Moderate" else "🟢"
    bar_filled         = round(score / 20 * 10)
    bar_visual         = "█" * bar_filled + "░" * (10 - bar_filled)

    # ── 1. HERO SCORE ────────────────────────────────────────
    st.markdown(
        f"""<div style='background:#0f0f1a;border:1px solid #1e1e3a;
            border-top:4px solid {score_color};border-radius:14px;
            padding:28px 32px;margin:12px 0 20px'>
          <div style='display:flex;align-items:center;gap:40px;flex-wrap:wrap'>
            <div style='text-align:center;min-width:120px'>
              <div style='color:{score_color};font-size:4rem;font-weight:900;
                   line-height:1;letter-spacing:-2px'>{score}</div>
              <div style='color:#444;font-size:1rem;font-weight:600'>/20</div>
              <div style='color:#333;font-family:monospace;font-size:0.95rem;
                   margin-top:4px'>{bar_visual}</div>
            </div>
            <div style='flex:1;min-width:180px'>
              <div style='color:{score_color};font-size:1.5rem;font-weight:800;
                   margin-bottom:6px'>{dec_emoji} {dec}</div>
              <div style='color:#555;font-size:0.85rem'>
                Risk level : <strong style='color:{score_color}'>{risk}</strong>
              </div>
              {f"<div style='color:#444;font-size:0.78rem;margin-top:8px'>🔍 {page_type_display[:60]}</div>" if page_type_display else ""}
            </div>
          </div>
        </div>""",
        unsafe_allow_html=True,
    )

    # ── 2. BREAKDOWN (4 barres) ──────────────────────────────
    criteria = [
        ("Hook",     c.get("hook",     0)),
        ("Offer",    c.get("offer",    0)),
        ("Trust",    c.get("trust",    0)),
        ("Friction", c.get("friction", 0)),
    ]
    bars_html = ""
    for lbl, val in criteria:
        col = "#FF4444" if val <= 2 else "#FF8C00" if val <= 3 else "#22c55e"
        pct = val / 5 * 100
        bars_html += f"""
        <div style='margin-bottom:10px'>
          <div style='display:flex;justify-content:space-between;margin-bottom:3px'>
            <span style='color:#aaa;font-size:0.82rem;font-weight:600'>{lbl}</span>
            <span style='color:{col};font-weight:700;font-size:0.85rem'>{val}/5</span>
          </div>
          <div style='background:#1a1a2e;border-radius:4px;height:6px'>
            <div style='background:{col};width:{pct}%;height:6px;border-radius:4px;
                 transition:width 0.3s'></div>
          </div>
        </div>"""
    st.markdown(
        f"<div style='background:#0f0f1a;border:1px solid #1e1e3a;border-radius:12px;"
        f"padding:20px 24px;margin-bottom:16px'>{bars_html}</div>",
        unsafe_allow_html=True,
    )

    if c.get("trust", 0) <= 2:
        st.caption("⚠️ Trust bas : LRS ne lit que le texte — vérifiez manuellement les preuves visuelles (photos, avis screenshots).")

    # ── 3. CVR ───────────────────────────────────────────────
    cv1, cv2, cv3 = st.columns(3)
    with cv1: st.metric("CVR actuel estimé",  c.get("cvr_cur", "—"))
    with cv2: st.metric("CVR post-fix",        c.get("cvr_fix", "—"))
    with cv3: st.metric("Uplift potentiel",    c.get("cvr_up",  "—"))
    st.caption("Benchmarks cold traffic — non garantis.")

    # ── 4. ANALYSE ───────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 🔬 Analyse détaillée")
    for key, lbl, val in [("hook_detail","Hook",c.get("hook",0)),
                           ("offer_detail","Offer",c.get("offer",0)),
                           ("trust_detail","Trust",c.get("trust",0)),
                           ("friction_detail","Friction",c.get("friction",0))]:
        detail = why.get(key, "")
        col    = "#FF4444" if val <= 2 else "#FF8C00" if val <= 3 else "#22c55e"
        if detail:
            with st.expander(f"{lbl} — {val}/5", expanded=(val <= 2)):
                st.markdown(detail)

    top3 = why.get("top_3_reasons", [])
    gaps = why.get("critical_gaps", [])
    if top3 or gaps:
        tg1, tg2 = st.columns(2)
        with tg1:
            if top3:
                st.markdown("**Top 3 raisons du score :**")
                for i, r in enumerate(top3, 1):
                    st.markdown(f"{i}. {r}")
        with tg2:
            if gaps:
                st.markdown("**Gaps critiques :**")
                for g in gaps:
                    st.markdown(f"- {g}")

    # ── 5. MESSAGE MATCH ─────────────────────────────────────
    if ms not in ("N/A", None, ""):
        st.markdown("---")
        st.markdown("#### 🔗 Message Match")
        mc = MATCH_COLORS.get(ms, "#888")
        st.markdown(f"<span style='color:{mc};font-weight:700;font-size:1.1rem'>{ms}</span>",
                    unsafe_allow_html=True)
        expl = mm.get("score_explication", "")
        if expl: st.caption(expl)
        mm_list = mm.get("mismatches", [])
        fixes   = mm.get("fix", [])
        if mm_list or fixes:
            ca, cb = st.columns(2)
            with ca:
                if mm_list:
                    st.markdown("**Mismatches :**")
                    for m2 in mm_list: st.markdown(f"- {m2}")
            with cb:
                if fixes:
                    st.markdown("**Corrections :**")
                    for f in fixes: st.markdown(f"- {f}")

    # ── 6. PLAN D'ACTION ─────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 🎯 Plan d'action")

    top_prio = fp.get("top_priority_action", {})
    if top_prio and top_prio.get("what"):
        st.markdown(
            f"""<div style='background:#1a0a0a;border:1px solid #FF4444;
                border-left:4px solid #FF4444;border-radius:10px;padding:16px 20px;margin-bottom:12px'>
              <div style='color:#FF4444;font-size:0.75rem;font-weight:700;
                   text-transform:uppercase;letter-spacing:1px;margin-bottom:6px'>
                Action prioritaire #1
              </div>
              <div style='color:#fff;font-weight:700;font-size:0.95rem;margin-bottom:8px'>
                {top_prio.get("what","")}
              </div>
              <div style='color:#aaa;font-size:0.85rem;line-height:1.6'>
                {top_prio.get("how_exactly","")}
              </div>
              <div style='color:#555;font-size:0.78rem;margin-top:8px'>
                Impact : {top_prio.get("expected_impact","")} &nbsp;·&nbsp;
                Temps : {top_prio.get("time_estimate","")}
              </div>
            </div>""",
            unsafe_allow_html=True,
        )

    quick_wins = fp.get("quick_wins", [])
    if quick_wins:
        st.markdown("**⚡ Quick Wins** *(< 1h)*")
        for qw in quick_wins:
            with st.expander("⚡ " + qw.get("what", "")):
                st.markdown("**Comment :** " + qw.get("how_exactly", ""))
                st.caption("Impact : " + qw.get("expected_impact","") + " · Temps : " + qw.get("time_estimate","<1h"))

    long_term = fp.get("long_term", [])
    if long_term:
        st.markdown("**🏗️ Long terme**")
        for lt in long_term:
            with st.expander("🏗️ " + lt.get("what", "")):
                st.markdown("**Comment :** " + lt.get("how_exactly", ""))
                st.caption("Impact : " + lt.get("expected_impact","") + " · Temps : " + lt.get("time_estimate",""))

    priority_actions = fp.get("priority_actions", [])
    if priority_actions:
        for a in priority_actions:
            imp = a.get("impact","medium")
            icon2 = "🔴" if imp=="high" else "🟡" if imp=="medium" else "🟢"
            cat   = a.get("category","")
            cat_l = " ⚡" if cat=="quick_win" else " 🏗️" if cat=="long_term" else ""
            with st.expander(f"{icon2}{cat_l} {a.get('what','')}"):
                st.markdown("**Comment :** " + a.get("how_exactly", a.get("how","")))
                if a.get("why"): st.caption("Pourquoi : " + a["why"])
                if a.get("time_estimate"): st.caption("Temps : " + a["time_estimate"])

    for t in fp.get("ab_tests", []):
        with st.expander("🧪 A/B : " + t.get("hypothesis", "")):
            ta, tb = st.columns(2)
            with ta: st.markdown("**A :** " + t.get("variant_a",""))
            with tb: st.markdown("**B :** " + t.get("variant_b",""))
            st.caption("Métrique : " + t.get("success_metric",""))

    # ── 6b. SCORE PREDICTION ─────────────────────────────────
    st.markdown("---")
    st.markdown("#### 🔮 Score Prediction — Si tu appliques le plan")

    # Gains réalistes par critère (cible = 4/5, réalisable à ~65%)
    h_gap = max(0, 4 - c["hook"])
    o_gap = max(0, 4 - c["offer"])
    t_gap = max(0, 4 - c["trust"])
    f_gap = max(0, 4 - c["friction"])
    h_gain = round(h_gap * 0.65)
    o_gain = round(o_gap * 0.65)
    t_gain = round(t_gap * 0.65)
    f_gain = round(f_gap * 0.65)
    total_gain    = h_gain + o_gain + t_gain + f_gain
    pred_score    = min(20, c["score"] + total_gain)
    pred_decision, _ = get_decision(pred_score)
    pred_color    = "#FF4444" if pred_score <= 9 else "#FF8C00" if pred_score <= 14 else "#22c55e"
    n_actions     = (1 if top_prio and top_prio.get("what") else 0) + len(quick_wins) + min(len(long_term), 2)

    # Card prediction
    gain_items = []
    if h_gain > 0: gain_items.append(f"Hook +{h_gain}")
    if o_gain > 0: gain_items.append(f"Offer +{o_gain}")
    if t_gain > 0: gain_items.append(f"Trust +{t_gain}")
    if f_gain > 0: gain_items.append(f"Friction +{f_gain}")

    gain_str = " · ".join(gain_items) if gain_items else "Score déjà optimal"
    pred_col1, pred_col2 = st.columns([2, 1])

    with pred_col1:
        pred_bars_html = ""
        crit_list = [
            ("Hook",     c["hook"],     h_gain, "#6366f1"),
            ("Offer",    c["offer"],    o_gain, "#22c55e"),
            ("Trust",    c["trust"],    t_gain, "#FF8C00"),
            ("Friction", c["friction"], f_gain, "#06b6d4"),
        ]
        for lbl, cur_v, gain_v, col_v in crit_list:
            cur_pct  = cur_v / 5 * 100
            gain_pct = min(100, (cur_v + gain_v) / 5 * 100)
            pred_bars_html += f"""
            <div style='margin-bottom:12px'>
              <div style='display:flex;justify-content:space-between;margin-bottom:4px'>
                <span style='color:#aaa;font-size:0.83em'>{lbl}</span>
                <span style='font-size:0.83em'>
                  <span style='color:#555'>{cur_v}/5</span>
                  {"&nbsp;→&nbsp;<span style='color:" + col_v + ";font-weight:700'>" + str(cur_v + gain_v) + "/5</span>" if gain_v > 0 else ""}
                </span>
              </div>
              <div style='background:#1a1a2e;border-radius:4px;height:6px;position:relative'>
                <div style='background:#2a2a4a;width:{gain_pct:.0f}%;height:6px;border-radius:4px;position:absolute'></div>
                <div style='background:{col_v};width:{cur_pct:.0f}%;height:6px;border-radius:4px;position:absolute'></div>
              </div>
            </div>"""
        st.markdown(
            f"""<div style='background:#0f0f1a;border:1px solid #1e1e3a;border-radius:10px;padding:16px 20px'>
              <div style='color:#888;font-size:0.75em;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px'>
                Potentiel d'amélioration — en appliquant {n_actions} action{"s" if n_actions > 1 else ""}
              </div>
              {pred_bars_html}
              <div style='color:#555;font-size:0.78em;margin-top:8px'>{gain_str}</div>
            </div>""",
            unsafe_allow_html=True,
        )

    with pred_col2:
        st.markdown(
            f"""<div style='background:#0f0f1a;border:1px solid #1e1e3a;
                border-top:4px solid {pred_color};border-radius:10px;
                padding:20px;text-align:center;height:100%'>
              <div style='color:#555;font-size:0.75em;text-transform:uppercase;letter-spacing:1px'>Score actuel</div>
              <div style='color:#888;font-size:2em;font-weight:700'>{c["score"]}<span style='color:#333;font-size:0.4em'>/20</span></div>
              <div style='color:#555;font-size:1.3em;margin:6px 0'>↓</div>
              <div style='color:#555;font-size:0.75em;text-transform:uppercase;letter-spacing:1px'>Score estimé</div>
              <div style='color:{pred_color};font-size:2.6em;font-weight:900;line-height:1'>
                {pred_score}<span style='color:#333;font-size:0.4em'>/20</span>
              </div>
              <div style='color:{pred_color};font-size:0.85em;font-weight:600;margin-top:4px'>{pred_decision}</div>
              <div style='color:#22c55e;font-size:0.88em;font-weight:700;margin-top:8px'>
                {"+" + str(total_gain) + " pts potentiels" if total_gain > 0 else "🏆 Déjà au maximum"}
              </div>
            </div>""",
            unsafe_allow_html=True,
        )

    # ── 7. REWRITE + ADS ─────────────────────────────────────
    st.markdown("---")
    rw_col, ads_col = st.columns(2)
    with rw_col:
        with st.expander("✍️ Rewrite recommandé"):
            if rw.get("headline"):    st.markdown("**Headline :**"); st.info(rw["headline"])
            if rw.get("subheadline"): st.markdown("**Sub :**");      st.info(rw["subheadline"])
            bullets = rw.get("hero_bullets", [])
            if bullets:
                st.markdown("**Bullets :**")
                for b in bullets: st.markdown(f"- {b}")
            if rw.get("cta_primary"):  st.markdown(f"**CTA :** `{rw['cta_primary']}`")
            if rw.get("guarantee"):    st.caption("Garantie : " + rw["guarantee"])
            for o in rw.get("offer_stack",[]): st.markdown(f"- {o}")
            for q in rw.get("faq_objections",[]): st.markdown(f"- {q}")
    with ads_col:
        with st.expander("📣 Ad Creative"):
            for a2 in ads.get("angles",[]):
                if isinstance(a2, dict):
                    st.markdown(f"- **{a2.get('angle','')}** — {a2.get('rationale','')}")
            for h in ads.get("hooks",[]):
                if isinstance(h, dict):
                    st.markdown(f"- `[{h.get('platform','')}/{h.get('type','')}]` {h.get('hook','')}")
            for i, v in enumerate(ads.get("variants",[]), 1):
                with st.expander(f"Variante {i} — {v.get('platform','')}"):
                    st.markdown("**Headline :** " + v.get("headline",""))
                    st.text_area("Primary Text", value=v.get("primary_text",""),
                                 height=110, disabled=True, key=f"pt_{i}")
                    st.markdown(f"**CTA :** `{v.get('cta','')}`")
            if ads.get("script_ugc_20s"):
                st.text_area("Script UGC 20-30s", value=ads["script_ugc_20s"],
                             height=150, disabled=True)

    with st.expander("🔧 JSON brut (debug)"):
        st.json(result)

# ── HISTORIQUE ───────────────────────────────────────────────
def render_history():
    st.subheader("Historique des Audits")
    if not st.session_state.audit_history:
        st.info("Aucun audit effectué dans cette session.")
        return

    history = st.session_state.audit_history

    # ── Bannière delta global ─────────────────────────────────
    if len(history) >= 2:
        first_score  = history[-1].get("score", 0)
        latest_score = history[0].get("score", 0)
        delta        = latest_score - first_score
        delta_str    = ("+" if delta >= 0 else "") + str(delta)
        delta_color  = "#22c55e" if delta > 0 else "#FF4444" if delta < 0 else "#888"
        avg_score    = round(sum(e.get("score", 0) for e in history) / len(history), 1)
        total_audits = len(history)

        st.markdown(
            f"""<div style='background:linear-gradient(135deg,#1a1a2e,#16213e);border-radius:12px;
                padding:18px 24px;margin-bottom:16px;display:flex;gap:32px;flex-wrap:wrap;align-items:center'>
              <div>
                <div style='color:#aaa;font-size:0.75em;text-transform:uppercase;letter-spacing:1px'>Progression globale</div>
                <div style='color:{delta_color};font-size:2.4em;font-weight:900;line-height:1'>{delta_str} pts</div>
                <div style='color:#555;font-size:0.85em'>depuis votre premier audit</div>
              </div>
              <div>
                <div style='color:#aaa;font-size:0.75em;text-transform:uppercase;letter-spacing:1px'>Score moyen</div>
                <div style='color:#6366f1;font-size:2em;font-weight:800'>{avg_score}<span style='font-size:0.5em;color:#555'>/20</span></div>
              </div>
              <div>
                <div style='color:#aaa;font-size:0.75em;text-transform:uppercase;letter-spacing:1px'>Total audits</div>
                <div style='color:#aaa;font-size:2em;font-weight:800'>{total_audits}</div>
              </div>
            </div>""",
            unsafe_allow_html=True,
        )

    # ── Graphique d'évolution des scores ─────────────────────
    if len(history) >= 2:
        st.markdown("#### 📈 Évolution des scores")
        history_reversed = list(reversed(history))
        chart_data = []
        for entry in history_reversed:
            label = (entry.get("url") or entry.get("offer_type") or "Audit")
            label = label.replace("https://", "").replace("http://", "")
            if len(label) > 30: label = label[:27] + "..."
            chart_data.append({
                "Audit": label,
                "Score /20": entry.get("score", 0),
                "Seuil Test (10)": 10,
                "Seuil Scale (15)": 15,
            })
        import pandas as pd
        df = pd.DataFrame(chart_data)
        st.line_chart(df.set_index("Audit")[["Score /20", "Seuil Test (10)", "Seuil Scale (15)"]])
        st.caption("Vert (15+) = Ready to scale · Orange (10+) = Test small budget · Rouge (<10) = Do NOT launch")
        st.markdown("---")

    for i, entry in enumerate(history):
        score  = entry.get("score", 0)
        dec    = entry.get("decision", "")
        label  = str(entry.get("url", "") or entry.get("offer_type", ""))[:40]
        color  = "#FF4444" if score <= 9 else "#FF8C00" if score <= 14 else "#22c55e"
        url_entry = entry.get("url", "")

        # Badge delta vs audit précédent (i+1 = plus ancien)
        delta_badge = ""
        if i + 1 < len(history):
            prev_score = history[i + 1].get("score", 0)
            d = score - prev_score
            if d != 0:
                dc = "#22c55e" if d > 0 else "#FF4444"
                delta_badge = f"  <span style='color:{dc};font-size:0.85em'>({'+'if d>0 else ''}{d})</span>"

        expander_title = (
            entry["timestamp"] + " — " + entry["mode"] +
            " — <span style='color:" + color + ";font-weight:700'>" + str(score) + "/20</span>" +
            delta_badge + " — " + label
        )

        with st.expander(f"{entry['timestamp']} — {entry['mode']} — {score}/20 — {label}"):
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("Score", str(score) + "/20")
            with c2:
                st.markdown("**Décision**<br><span style='color:" + color + "'>" + dec + "</span>", unsafe_allow_html=True)
            with c3:
                st.markdown("**Plateforme**<br>" + entry.get("platform", ""), unsafe_allow_html=True)
            with c4:
                if i + 1 < len(history):
                    prev = history[i + 1].get("score", 0)
                    d2 = score - prev
                    dc2 = "#22c55e" if d2 > 0 else "#FF4444" if d2 < 0 else "#888"
                    ds = ("+" if d2 >= 0 else "") + str(d2) + " pts"
                    st.markdown("**vs précédent**<br><span style='color:" + dc2 + ";font-weight:700'>" + ds + "</span>", unsafe_allow_html=True)

            # ── Tracker d'implémentation ──────────────────────
            result_entry = entry.get("result", {})
            fp_e = result_entry.get("fix_plan", {})
            recs = []
            top_p = fp_e.get("top_priority_action", {})
            if top_p and top_p.get("what"):
                recs.append(("🎯 " + top_p.get("what", "")[:70], "top_" + str(i)))
            for j, qw in enumerate(fp_e.get("quick_wins", [])[:4]):
                recs.append(("⚡ " + qw.get("what", "")[:70], "qw_" + str(i) + "_" + str(j)))
            for j, lt in enumerate(fp_e.get("long_term", [])[:3]):
                recs.append(("🏗️ " + lt.get("what", "")[:70], "lt_" + str(i) + "_" + str(j)))

            if recs:
                st.markdown("**📋 Suivi des recommandations :**")
                tracker_key = "impl_" + str(i)
                if tracker_key not in st.session_state.impl_tracker:
                    st.session_state.impl_tracker[tracker_key] = {}
                done_count = 0
                for rec_label, rec_id in recs:
                    checked = st.checkbox(
                        rec_label,
                        value=st.session_state.impl_tracker[tracker_key].get(rec_id, False),
                        key="impl_chk_" + rec_id,
                    )
                    st.session_state.impl_tracker[tracker_key][rec_id] = checked
                    if checked: done_count += 1
                pct_impl = int(done_count / len(recs) * 100)
                st.progress(pct_impl / 100)
                st.caption(f"{done_count}/{len(recs)} recommandations appliquées ({pct_impl}%)")
                if pct_impl >= 80:
                    st.success("🎉 Excellent ! Lancez un re-audit pour mesurer votre progression.")
                elif pct_impl >= 40:
                    st.info("💡 Bon départ — une fois tout appliqué, re-auditez pour valider l'impact.")

            st.markdown("---")

            # ── Boutons d'action ─────────────────────────────
            btn1, btn2, btn3 = st.columns(3)
            with btn1:
                if st.button("🔄 Recharger résultats", key="reload_" + str(i)):
                    st.session_state.loaded_result = entry["result"]
                    st.rerun()
            with btn2:
                can_reaudit = bool(url_entry or entry.get("ad_text"))
                if can_reaudit and st.button("🚀 Re-audit 1-clic", key="reaudit1c_" + str(i),
                                              help="Relance l'audit avec exactement les mêmes paramètres — sans rien retaper",
                                              type="primary"):
                    st.session_state.auto_reaudit_idx = i
                    st.rerun()
            with btn3:
                if st.button("🔗 Pré-remplir formulaire", key="reaudit_" + str(i),
                              help="Ouvre le formulaire pré-rempli dans l'onglet Audit"):
                    st.session_state.reaudit_url = url_entry
                    st.rerun()

            fname_base = "LRS_" + entry["timestamp"].replace("/","-").replace(":","-").replace(" ","_")
            ecA, ecB, ecC, ecD = st.columns(4)
            with ecA:
                txt = export_txt(entry["result"], entry)
                st.download_button("📥 .txt", data=txt.encode("utf-8"),
                                   file_name=fname_base+".txt", mime="text/plain",
                                   key="exp_"+str(i))
            with ecB:
                if PDF_AVAILABLE:
                    try:
                        entry_meta = {**entry, "version": APP_VERSION}
                        pdf_b = generate_pdf_report(entry["result"], entry_meta)
                        st.download_button("📄 PDF", data=pdf_b,
                                           file_name=fname_base+".pdf", mime="application/pdf",
                                           key="exppdf_"+str(i))
                    except Exception:
                        pass
            with ecC:
                if PDF_AVAILABLE:
                    try:
                        client_name = st.text_input("Nom client", key="client_" + str(i),
                                                     placeholder="Ex: Startup XYZ", label_visibility="collapsed")
                        entry_meta_c = {**entry, "version": APP_VERSION,
                                        "client_name": client_name or "",
                                        "report_mode": "client"}
                        pdf_c = generate_pdf_report(entry["result"], entry_meta_c)
                        st.download_button("👔 Client", data=pdf_c,
                                           file_name=fname_base+"_client.pdf", mime="application/pdf",
                                           key="exppdf_client_"+str(i))
                    except Exception:
                        pass
            with ecD:
                render_email_widget(entry["result"], entry, key_prefix=f"hist_email_{i}")
            # Share below the 4-col row
            share_s1, share_s2 = st.columns(2)
            with share_s1:
                render_share_widget(entry["result"], entry, key_prefix=f"hist_share_{i}")
            with share_s2:
                pass

        # ── Re-audit 1-clic inline ────────────────────────────
        if st.session_state.get("auto_reaudit_idx") == i:
            st.markdown("---")
            st.markdown("#### 🚀 Re-audit en cours...")
            with st.status("🧠 LRS ré-analyse votre page...", expanded=True) as _ra_status:
                _ra_stage  = st.empty()
                _ra_tokens = st.empty()
                try:
                    ra_mode    = entry.get("mode", "Funnel Only")
                    ra_url     = entry.get("url", "")
                    ra_plat    = entry.get("platform", "Meta")
                    ra_offer   = entry.get("offer_type", "Digital product")
                    ra_brand   = entry.get("brand_type", "Nouveau lancement")
                    ra_model   = entry.get("model", "gpt-4o-mini")
                    ra_ad      = entry.get("ad_text", "")
                    ra_mkt     = entry.get("market_context", "")

                    ra_content = ""
                    if ra_mode in ("Funnel Only", "Full Risk") and ra_url:
                        _ra_stage.markdown(
                            "<div style='padding:8px 12px;background:#1a1a2e;border-radius:6px;"
                            "border-left:3px solid #6366f1;color:#ccc;font-size:0.88em'>"
                            "🔍 Extraction de la page...</div>",
                            unsafe_allow_html=True
                        )
                        ra_content, _, _ = extract_page(ra_url)

                    ra_pt = detect_page_type(ra_content, ra_url) if ra_content else entry.get("page_type", "Landing page")
                    ra_pl = detect_language(ra_content) if ra_content else "fr"

                    new_result = run_audit_stream(
                        ra_mode, ra_plat, ra_offer, ra_content, ra_ad, ra_mkt,
                        ra_model, brand_type=ra_brand, page_type=ra_pt, page_lang=ra_pl,
                        status_stage=_ra_stage, status_tokens=_ra_tokens,
                    )
                    ts_ra = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                    new_meta = {
                        "mode": ra_mode, "platform": ra_plat, "offer_type": ra_offer,
                        "url": ra_url, "timestamp": ts_ra, "brand_type": ra_brand,
                        "page_type": ra_pt, "ad_text": ra_ad, "model": ra_model,
                        "market_context": ra_mkt,
                    }
                    save_history(new_result, new_meta)
                    st.session_state.auto_reaudit_idx = None
                    _ra_status.update(label="✅ Re-audit terminé !", state="complete", expanded=False)
                    _ra_tokens.empty()

                    # Score delta immédiat
                    prev_score = entry.get("score", 0)
                    new_score  = new_result.get("_c", {}).get("score", 0)
                    delta_ra   = new_score - prev_score
                    dc_ra      = "#22c55e" if delta_ra > 0 else "#FF4444" if delta_ra < 0 else "#888"
                    sign_ra    = "+" if delta_ra > 0 else ""
                    st.markdown(
                        f"""<div style='background:#0f0f1a;border:1px solid #1e1e3a;border-radius:10px;
                            padding:16px 20px;margin:12px 0;display:flex;gap:24px;align-items:center'>
                          <div>
                            <div style='color:#888;font-size:0.75em;text-transform:uppercase'>Avant</div>
                            <div style='color:#aaa;font-size:1.8em;font-weight:700'>{prev_score}<span style='color:#555;font-size:0.5em'>/20</span></div>
                          </div>
                          <div style='color:#555;font-size:1.5em'>→</div>
                          <div>
                            <div style='color:#888;font-size:0.75em;text-transform:uppercase'>Après</div>
                            <div style='color:{dc_ra};font-size:1.8em;font-weight:700'>{new_score}<span style='color:#555;font-size:0.5em'>/20</span></div>
                          </div>
                          <div style='color:{dc_ra};font-size:1.4em;font-weight:800'>{sign_ra}{delta_ra} pts</div>
                        </div>""",
                        unsafe_allow_html=True,
                    )
                    render_results(new_result)

                except Exception as e_ra:
                    _ra_status.update(label="❌ Erreur", state="error", expanded=False)
                    st.error(f"Erreur re-audit : {e_ra}")
                    st.session_state.auto_reaudit_idx = None


# ── ONGLET MONITORING (Schedule + Alertes + Score Trend) ─────
def render_monitoring(api_key):
    st.subheader("📡 Monitoring — Audits Planifiés & Alertes")

    history  = st.session_state.audit_history
    schedule = st.session_state.schedule
    alerts   = compute_score_alerts(history)

    # ── Bandeau alertes ──────────────────────────────────────
    if alerts:
        st.markdown("#### 🚨 Alertes Score")
        for al in alerts[:5]:
            url_short = al["url"].replace("https://","").replace("http://","")[:50]
            delta     = al["delta"]
            icon      = "📈" if delta > 0 else "📉"
            col_al    = "#22c55e" if delta > 0 else "#FF4444"
            sign      = "+" if delta > 0 else ""
            st.markdown(
                f"""<div style='background:#1a1a2e;border-left:4px solid {col_al};
                    border-radius:8px;padding:12px 16px;margin:4px 0;
                    display:flex;gap:16px;align-items:center'>
                  <span style='font-size:1.5em'>{icon}</span>
                  <div style='flex:1'>
                    <span style='color:#ccc;font-size:0.9em'>{url_short}</span><br>
                    <span style='color:#888;font-size:0.78em'>{al['latest_ts']}</span>
                  </div>
                  <div style='text-align:right'>
                    <span style='color:#888'>{al['prev_score']}/20</span>
                    <span style='color:#555'> → </span>
                    <span style='color:{col_al};font-weight:700'>{al['latest_score']}/20</span>
                    <span style='color:{col_al};font-size:0.85em'> ({sign}{delta} pts)</span>
                  </div>
                </div>""",
                unsafe_allow_html=True,
            )
        st.markdown("")
    else:
        st.info("Aucune alerte — aucune variation significative (≥2 pts) détectée entre les derniers audits.")

    st.markdown("---")

    # ── Score Trend par Page ──────────────────────────────────
    st.markdown("#### 📈 Score Trend par Page")

    url_map = {}
    for entry in reversed(history):
        url = entry.get("url", "")
        if not url: continue
        url_map.setdefault(url, []).append(entry)

    tracked_urls = {u: entries for u, entries in url_map.items() if len(entries) >= 2}

    if not tracked_urls:
        st.caption("Auditez la même URL plusieurs fois pour voir son évolution ici.")
    else:
        sel_url = st.selectbox(
            "Choisir une page suivie",
            list(tracked_urls.keys()),
            format_func=lambda u: u.replace("https://","").replace("http://","")[:60],
            key="trend_url_sel",
        )
        if sel_url:
            entries_url = tracked_urls[sel_url]
            import pandas as pd
            chart_data = []
            for e in entries_url:
                chart_data.append({
                    "Date":          e.get("timestamp", ""),
                    "Score /20":     e.get("score", 0),
                    "Seuil Test":    10,
                    "Seuil Scale":   15,
                })
            df_trend = pd.DataFrame(chart_data)
            st.line_chart(df_trend.set_index("Date")[["Score /20", "Seuil Test", "Seuil Scale"]])

            first_sc = entries_url[0].get("score", 0)
            last_sc  = entries_url[-1].get("score", 0)
            delta_t  = last_sc - first_sc
            col_t    = "#22c55e" if delta_t > 0 else "#FF4444" if delta_t < 0 else "#888"
            sign_t   = "+" if delta_t >= 0 else ""
            met1, met2, met3 = st.columns(3)
            with met1: st.metric("Premier audit", f"{first_sc}/20")
            with met2: st.metric("Dernier audit",  f"{last_sc}/20")
            with met3: st.metric("Progression totale", f"{sign_t}{delta_t} pts",
                                  delta=delta_t, delta_color="normal")

    st.markdown("---")

    # ── Gestion des audits planifiés ─────────────────────────
    st.markdown("#### ⏰ Audits Planifiés Automatiques")
    st.caption("L'app vérifie les audits en retard à chaque ouverture et les exécute automatiquement.")

    with st.expander("➕ Planifier un audit", expanded=(len(schedule) == 0)):
        sc_url  = st.text_input("URL à surveiller", placeholder="https://ma-landing.com", key="sc_url")
        sc_freq = st.selectbox("Fréquence", ["7 jours", "14 jours", "30 jours"], key="sc_freq")
        freq_map = {"7 jours": 7, "14 jours": 14, "30 jours": 30}

        sc1, sc2 = st.columns(2)
        with sc1:
            sc_mode   = st.selectbox("Mode", ["Funnel Only","Full Risk"], key="sc_mode")
            sc_plat   = st.selectbox("Plateforme", ["Meta","TikTok","Google","Mixed"], key="sc_plat")
        with sc2:
            sc_offer  = st.selectbox("Offre", ["Digital product","Ecom (produit physique)"], key="sc_offer")
            sc_brand  = st.radio("Marque", ["Nouveau lancement","Marque etablie"], key="sc_brand", horizontal=True)

        if st.button("⏰ Planifier", type="primary", key="btn_schedule"):
            if not sc_url.strip():
                st.error("Renseignez une URL.")
            else:
                sid = "sc_" + str(int(time.time()))
                schedule[sid] = {
                    "url":        sc_url.strip(),
                    "freq_days":  freq_map[sc_freq],
                    "mode":       sc_mode,
                    "platform":   sc_plat,
                    "offer_type": sc_offer,
                    "brand_type": sc_brand,
                    "enabled":    True,
                    "last_run":   "",
                    "last_score": None,
                    "last_error": "",
                    "created":    datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
                }
                save_schedule(schedule)
                st.session_state.schedule = schedule
                st.success(f"Audit planifié toutes les {sc_freq} pour {sc_url.strip()[:40]}")
                st.rerun()

    if schedule:
        st.markdown("**Audits en cours de surveillance :**")
        for sid, sched in list(schedule.items()):
            url_s     = sched.get("url","")[:50]
            freq      = sched.get("freq_days", 7)
            last_run  = sched.get("last_run","Jamais")
            last_sc   = sched.get("last_score")
            enabled   = sched.get("enabled", True)
            err       = sched.get("last_error","")

            # Calcul prochain audit
            try:
                lr_dt = datetime.datetime.strptime(last_run, "%d/%m/%Y %H:%M") if last_run != "Jamais" else None
                if lr_dt:
                    next_run = lr_dt + datetime.timedelta(days=freq)
                    days_left = (next_run - datetime.datetime.now()).days
                    next_str  = f"dans {days_left}j" if days_left > 0 else "à la prochaine ouverture"
                else:
                    next_str = "à la prochaine ouverture"
            except Exception:
                next_str = "N/A"

            sc_icon = ("🟢" if (last_sc or 0) >= 15 else "🟡" if (last_sc or 0) >= 10 else "🔴") if last_sc is not None else "⚪"
            status_icon = "✅" if enabled else "⏸️"

            with st.expander(f"{status_icon} {url_s} — toutes les {freq}j — {sc_icon} {last_sc}/20 si disponible" if last_sc else f"{status_icon} {url_s} — toutes les {freq}j — pas encore audité"):
                col_s1, col_s2, col_s3 = st.columns(3)
                with col_s1:
                    st.markdown(f"**Dernier audit :** {last_run}")
                    if last_sc is not None:
                        st.markdown(f"**Dernier score :** {last_sc}/20")
                with col_s2:
                    st.markdown(f"**Prochain audit :** {next_str}")
                    st.markdown(f"**Mode :** {sched.get('mode','')}")
                with col_s3:
                    if err:
                        st.error(f"Erreur : {err[:80]}")
                    # Forcer re-run
                    if st.button("▶️ Lancer maintenant", key="sc_run_" + sid):
                        with st.spinner("Audit en cours..."):
                            try:
                                content, status, _ = extract_page(url_s if len(url_s) < 50 else sched.get("url",""))
                                if content:
                                    pt  = detect_page_type(content, sched.get("url",""))
                                    pl  = detect_language(content)
                                    res = run_audit(sched.get("mode","Funnel Only"), sched.get("platform","Meta"),
                                                   sched.get("offer_type","Digital product"), content, "",
                                                   "", "gpt-4o-mini", brand_type=sched.get("brand_type","Nouveau lancement"),
                                                   page_type=pt, page_lang=pl)
                                    ts_now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                                    meta_s = {"url": sched.get("url",""), "mode": sched.get("mode",""),
                                              "platform": sched.get("platform",""), "offer_type": sched.get("offer_type",""),
                                              "brand_type": sched.get("brand_type",""), "page_type": pt,
                                              "timestamp": ts_now, "scheduled": True}
                                    save_history(res, meta_s)
                                    schedule[sid]["last_run"]   = ts_now
                                    schedule[sid]["last_score"] = res.get("_c",{}).get("score",0)
                                    schedule[sid]["last_error"] = ""
                                    save_schedule(schedule)
                                    st.session_state.schedule = schedule
                                    st.success(f"Audit terminé : {res.get('_c',{}).get('score',0)}/20")
                                    st.rerun()
                            except Exception as e:
                                st.error(str(e))

                act1, act2 = st.columns(2)
                with act1:
                    tog_label = "⏸️ Désactiver" if enabled else "▶️ Activer"
                    if st.button(tog_label, key="sc_tog_" + sid):
                        schedule[sid]["enabled"] = not enabled
                        save_schedule(schedule)
                        st.session_state.schedule = schedule
                        st.rerun()
                with act2:
                    if st.button("🗑️ Supprimer", key="sc_del_" + sid):
                        del schedule[sid]
                        save_schedule(schedule)
                        st.session_state.schedule = schedule
                        st.rerun()
    else:
        st.caption("Aucun audit planifié.")

# ── PROJETS MULTI-PAGES ──────────────────────────────────────
def render_projects(api_key):
    st.subheader("🗂️ Projets Multi-Pages")
    st.caption("Groupez plusieurs URLs d'un même funnel sous un projet. Obtenez un score global et identifiez le maillon faible.")

    projects = st.session_state.projects

    # ── Créer un nouveau projet ───────────────────────────────
    with st.expander("➕ Créer un nouveau projet", expanded=(len(projects) == 0)):
        proj_name = st.text_input("Nom du projet", placeholder="Ex: Funnel Produit X / Client Startup Y", key="new_proj_name")
        proj_notes = st.text_area("Notes (optionnel)", placeholder="Contexte, objectifs, budget...", key="new_proj_notes", height=70)

        st.markdown("**URLs du funnel (une par ligne) :**")
        proj_urls_raw = st.text_area(
            "URLs",
            placeholder="https://ma-pub.com\nhttps://ma-landing.com\nhttps://ma-page-commande.com",
            key="new_proj_urls", height=100, label_visibility="collapsed"
        )

        col_save, col_ = st.columns([1, 3])
        with col_save:
            if st.button("💾 Créer le projet", type="primary", key="create_proj"):
                if not proj_name.strip():
                    st.error("Donnez un nom au projet.")
                else:
                    urls_list = [u.strip() for u in proj_urls_raw.strip().splitlines() if u.strip()]
                    if not urls_list:
                        st.error("Ajoutez au moins une URL.")
                    else:
                        new_proj = {
                            "name": proj_name.strip(),
                            "notes": proj_notes.strip(),
                            "urls": urls_list,
                            "created": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "audits": {},  # url → {score, decision, timestamp}
                        }
                        projects[proj_name.strip()] = new_proj
                        save_projects(projects)
                        st.session_state.projects = projects
                        st.success(f"Projet '{proj_name}' créé avec {len(urls_list)} URLs !")
                        st.rerun()

    if not projects:
        st.info("Aucun projet créé. Créez votre premier projet ci-dessus.")
        return

    st.markdown("---")

    # ── Liste des projets ─────────────────────────────────────
    for proj_key, proj in list(projects.items()):
        audits   = proj.get("audits", {})
        urls     = proj.get("urls", [])
        n_done   = len([u for u in urls if u in audits])
        avg_sc   = round(sum(audits[u]["score"] for u in urls if u in audits) / n_done, 1) if n_done > 0 else None
        proj_color = "#22c55e" if (avg_sc or 0) >= 15 else "#FF8C00" if (avg_sc or 0) >= 10 else "#FF4444"

        expander_label = (
            f"🗂️ {proj['name']}  —  {n_done}/{len(urls)} audités"
            + (f"  —  Moy {avg_sc}/20" if avg_sc is not None else "  —  Non audité")
        )

        with st.expander(expander_label, expanded=(n_done < len(urls))):
            if proj.get("notes"):
                st.caption(proj["notes"])

            # Score global + maillon faible
            if n_done > 0:
                scores_list = [(u, audits[u]["score"]) for u in urls if u in audits]
                weakest = min(scores_list, key=lambda x: x[1])
                strongest = max(scores_list, key=lambda x: x[1])

                mc1, mc2, mc3 = st.columns(3)
                with mc1:
                    st.metric("Score moyen", f"{avg_sc}/20")
                with mc2:
                    wk_short = weakest[0].replace("https://","")[:30]
                    st.metric("🔴 Maillon faible", f"{weakest[1]}/20", delta=wk_short, delta_color="inverse")
                with mc3:
                    st_short = strongest[0].replace("https://","")[:30]
                    st.metric("🟢 Meilleur", f"{strongest[1]}/20", delta=st_short)

                # Barre de progression des URLs
                st.markdown("**Progression des pages :**")
                for u in urls:
                    u_short = u.replace("https://","").replace("http://","")[:50]
                    if u in audits:
                        sc = audits[u]["score"]
                        col = "#22c55e" if sc >= 15 else "#FF8C00" if sc >= 10 else "#FF4444"
                        st.markdown(
                            f"<div style='display:flex;align-items:center;gap:12px;margin:4px 0'>"
                            f"<span style='color:#aaa;font-size:0.85em;min-width:200px'>{u_short}</span>"
                            f"<span style='color:{col};font-weight:700'>{sc}/20</span>"
                            f"<span style='color:#555;font-size:0.8em'>{audits[u].get('decision','')}</span>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            f"<div style='display:flex;align-items:center;gap:12px;margin:4px 0'>"
                            f"<span style='color:#555;font-size:0.85em;min-width:200px'>{u_short}</span>"
                            f"<span style='color:#555'>— non audité</span>"
                            f"</div>",
                            unsafe_allow_html=True
                        )

                st.markdown("")

            # ── Bouton Auditer tout le projet ─────────────────
            audit_opts_col, del_col = st.columns([3, 1])
            with audit_opts_col:
                proj_mode   = st.selectbox("Mode", ["Funnel Only", "Full Risk"], key="pm_" + proj_key)
                proj_plat   = st.selectbox("Plateforme", ["Meta", "TikTok", "Google", "Mixed"], key="pp_" + proj_key)
                proj_offer  = st.selectbox("Offre", ["Digital product", "Ecom (produit physique)"], key="po_" + proj_key)
                proj_brand  = st.radio("Marque", ["Nouveau lancement", "Marque etablie"], key="pb_" + proj_key, horizontal=True)

                urls_to_audit = [u for u in urls if u not in audits]
                btn_label = (f"▶️ Auditer les {len(urls_to_audit)} pages restantes"
                             if urls_to_audit else "🔁 Re-auditer toutes les pages")

                if st.button(btn_label, key="run_proj_" + proj_key, type="primary"):
                    targets = urls_to_audit if urls_to_audit else urls
                    progress_bar = st.progress(0)
                    for idx_u, u in enumerate(targets):
                        with st.spinner(f"Auditing {u.replace('https://','')[:40]}..."):
                            content, status, is_js = extract_page(u)
                            if not content:
                                st.warning(f"Impossible d'extraire {u}: {status}")
                                continue
                            pt  = detect_page_type(content, u)
                            pl  = detect_language(content)
                            try:
                                res = run_audit(proj_mode, proj_plat, proj_offer, content, "",
                                               "", "gpt-4o-mini", brand_type=proj_brand,
                                               page_type=pt, page_lang=pl)
                                c_r = res.get("_c", {})
                                projects[proj_key]["audits"][u] = {
                                    "score": c_r.get("score", 0),
                                    "decision": c_r.get("decision", ""),
                                    "timestamp": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
                                }
                                save_projects(projects)
                                st.session_state.projects = projects
                                meta_p = {"url": u, "mode": proj_mode, "platform": proj_plat,
                                          "offer_type": proj_offer, "brand_type": proj_brand,
                                          "page_type": pt, "timestamp": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")}
                                save_history(res, meta_p)
                            except Exception as e2:
                                st.error(f"Erreur audit {u}: {e2}")
                        progress_bar.progress((idx_u + 1) / len(targets))
                    st.success("Projet audité ! Consultez les résultats dans l'Historique.")
                    st.rerun()

            with del_col:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️ Supprimer", key="del_proj_" + proj_key):
                    del projects[proj_key]
                    save_projects(projects)
                    st.session_state.projects = projects
                    st.rerun()

# ── BULK AUDIT ───────────────────────────────────────────────
def render_bulk(api_key):
    st.subheader("⚡ Bulk Audit — Plusieurs URLs en 1 clic")
    st.caption("Collez jusqu'à 20 URLs (une par ligne) ou importez un CSV. LRS audite tout et génère un tableau comparatif.")

    bulk_tab_input, bulk_tab_csv = st.tabs(["✏️ Saisie manuelle", "📄 Import CSV"])

    with bulk_tab_input:
        urls_raw = st.text_area(
            "URLs (une par ligne)",
            placeholder="https://page1.com\nhttps://page2.com\nhttps://concurrent.com",
            height=160,
            key="bulk_urls_input",
        )
        urls_list = [u.strip() for u in urls_raw.strip().splitlines() if u.strip().startswith("http")]

    with bulk_tab_csv:
        uploaded_csv = st.file_uploader("Importer un CSV (colonne 'url')", type=["csv","txt"], key="bulk_csv_upload")
        if uploaded_csv:
            try:
                import io as _io
                content_csv = uploaded_csv.read().decode("utf-8", errors="ignore")
                lines = content_csv.splitlines()
                # Détecter si CSV avec header ou liste brute
                csv_urls = []
                for line in lines:
                    parts = line.split(",")
                    for part in parts:
                        part = part.strip().strip('"').strip("'")
                        if part.startswith("http"):
                            csv_urls.append(part)
                if csv_urls:
                    st.success(f"{len(csv_urls)} URLs détectées dans le fichier.")
                    urls_list = csv_urls
                else:
                    st.warning("Aucune URL valide trouvée dans le fichier.")
            except Exception as e:
                st.error(f"Erreur lecture CSV : {e}")

    bc1, bc2, bc3 = st.columns(3)
    with bc1: bulk_mode   = st.selectbox("Mode",      ["Funnel Only","Full Risk"], key="bulk_mode")
    with bc2: bulk_plat   = st.selectbox("Plateforme",["Meta","TikTok","Google","Mixed"], key="bulk_plat")
    with bc3: bulk_offer  = st.selectbox("Offre",     ["Digital product","Ecom (produit physique)"], key="bulk_offer")
    bulk_brand = st.radio("Marque", ["Nouveau lancement","Marque etablie"], key="bulk_brand", horizontal=True)

    n_urls = len(urls_list) if 'urls_list' in dir() and urls_list else 0
    btn_label = f"⚡ Lancer {n_urls} audits" if n_urls > 0 else "⚡ Lancer les audits"
    run_bulk  = st.button(btn_label, type="primary", use_container_width=True, key="run_bulk_btn",
                           disabled=(n_urls == 0))

    if run_bulk and n_urls > 0:
        if n_urls > 20:
            st.warning("Maximum 20 URLs par batch. Seules les 20 premières seront auditées.")
            urls_list = urls_list[:20]

        bulk_results = []
        progress_bar = st.progress(0)
        status_text  = st.empty()

        for idx, url in enumerate(urls_list):
            status_text.markdown(f"🔍 Auditing **{url.replace('https://','')[:50]}**... ({idx+1}/{len(urls_list)})")
            try:
                content, status, is_js = extract_page(url)
                if not content:
                    bulk_results.append({"url": url, "error": status, "score": None})
                    progress_bar.progress((idx+1)/len(urls_list))
                    continue
                pt  = detect_page_type(content, url)
                pl  = detect_language(content)
                res = run_audit(bulk_mode, bulk_plat, bulk_offer, content, "",
                               "", "gpt-4o-mini", brand_type=bulk_brand,
                               page_type=pt, page_lang=pl)
                c_r = res.get("_c", {})
                ts  = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                meta_b = {"url": url, "mode": bulk_mode, "platform": bulk_plat,
                          "offer_type": bulk_offer, "brand_type": bulk_brand,
                          "page_type": pt, "timestamp": ts}
                save_history(res, meta_b)
                bulk_results.append({
                    "url": url,
                    "score": c_r.get("score", 0),
                    "hook": c_r.get("hook", 0),
                    "offer": c_r.get("offer", 0),
                    "trust": c_r.get("trust", 0),
                    "friction": c_r.get("friction", 0),
                    "decision": c_r.get("decision", ""),
                    "risk": c_r.get("risk", "High"),
                    "page_type": pt,
                    "result": res,
                    "error": None,
                })
            except Exception as e:
                bulk_results.append({"url": url, "error": str(e)[:80], "score": None})
            progress_bar.progress((idx+1)/len(urls_list))

        status_text.empty()
        st.session_state.bulk_results = bulk_results
        st.rerun()

    # ── Affichage résultats bulk ──────────────────────────────
    if st.session_state.bulk_results:
        results = st.session_state.bulk_results
        st.markdown("---")
        st.markdown(f"### Résultats — {len(results)} pages auditées")

        # Trier par score décroissant
        sortable = [r for r in results if r.get("score") is not None]
        errors   = [r for r in results if r.get("score") is None]
        sortable.sort(key=lambda r: r["score"], reverse=True)

        # Tableau récap
        import pandas as pd
        rows_df = []
        for r in sortable:
            sc    = r["score"]
            emoji = "🟢" if sc >= 15 else "🟡" if sc >= 10 else "🔴"
            rows_df.append({
                "Rang": sortable.index(r)+1,
                "URL":  r["url"].replace("https://","")[:50],
                "Score": f"{emoji} {sc}/20",
                "Hook":  f"{r.get('hook',0)}/5",
                "Offer": f"{r.get('offer',0)}/5",
                "Trust": f"{r.get('trust',0)}/5",
                "Friction": f"{r.get('friction',0)}/5",
                "Décision": r.get("decision",""),
            })
        if rows_df:
            df_bulk = pd.DataFrame(rows_df)
            st.dataframe(df_bulk, use_container_width=True, hide_index=True)

        # Podium top 3
        if len(sortable) >= 3:
            st.markdown("#### 🏆 Podium")
            p1, p2, p3 = st.columns(3)
            for col, rank, entry in [(p2, 2, sortable[1]), (p1, 1, sortable[0]), (p3, 3, sortable[2])]:
                with col:
                    sc_c = "#FFD700" if rank==1 else "#C0C0C0" if rank==2 else "#CD7F32"
                    medal = "🥇" if rank==1 else "🥈" if rank==2 else "🥉"
                    url_s = entry["url"].replace("https://","")[:35]
                    sc_h  = "#22c55e" if entry["score"]>=15 else "#FF8C00" if entry["score"]>=10 else "#FF4444"
                    st.markdown(
                        f"""<div style='background:#1a1a2e;border:2px solid {sc_c};border-radius:10px;
                            padding:14px;text-align:center;margin:4px'>
                          <div style='font-size:1.8em'>{medal}</div>
                          <div style='color:#888;font-size:0.75em;margin:4px 0'>{url_s}</div>
                          <div style='color:{sc_h};font-size:2em;font-weight:900'>{entry['score']}<span style='color:#555;font-size:0.5em'>/20</span></div>
                          <div style='color:{sc_h};font-size:0.8em'>{entry.get('decision','')}</div>
                        </div>""",
                        unsafe_allow_html=True,
                    )

        # Détail par URL
        st.markdown("#### 📋 Détail par page")
        for r in sortable:
            sc = r["score"]
            sc_color = "#22c55e" if sc >= 15 else "#FF8C00" if sc >= 10 else "#FF4444"
            with st.expander(f"{r['url'].replace('https://','')[:55]} — {sc}/20 — {r.get('decision','')}"):
                render_results(r["result"])

        if errors:
            st.markdown("#### ⚠️ Erreurs")
            for e in errors:
                st.error(f"{e['url']} : {e.get('error','Erreur inconnue')}")

        # Export CSV résultats
        if sortable:
            import csv as _csv
            import io as _io2
            out = _io2.StringIO()
            writer = _csv.DictWriter(out, fieldnames=["url","score","hook","offer","trust","friction","decision","risk","page_type"])
            writer.writeheader()
            for r in sortable:
                writer.writerow({k: r.get(k,"") for k in ["url","score","hook","offer","trust","friction","decision","risk","page_type"]})
            st.download_button("📥 Exporter résultats CSV", data=out.getvalue().encode("utf-8"),
                               file_name="LRS_bulk_results.csv", mime="text/csv",
                               use_container_width=True)

        if st.button("🗑️ Vider les résultats", key="clear_bulk"):
            st.session_state.bulk_results = []
            st.rerun()

# ── COMPARAISON 2 URLs ───────────────────────────────────────
def render_comparison(api_key, model="gpt-4o-mini"):
    st.subheader("Mode Comparaison — 2 URLs côte à côte")
    st.caption("Auditez 2 pages en simultané pour comparer vos scores : votre page vs concurrent, avant vs après refonte, etc.")

    c1, c2 = st.columns(2)
    with c1:
        url_a = st.text_input("URL Page A", placeholder="https://votre-page.com", key="comp_url_a")
        label_a = st.text_input("Label A", value="Ma page", key="comp_label_a")
    with c2:
        url_b = st.text_input("URL Page B", placeholder="https://concurrent.com", key="comp_url_b")
        label_b = st.text_input("Label B", value="Concurrent", key="comp_label_b")

    mode_c       = st.selectbox("Mode", ["Funnel Only","Full Risk"], key="comp_mode")
    platform_c   = st.selectbox("Plateforme", ["Meta","TikTok","Google","Mixed"], key="comp_plat")
    offer_type_c = st.selectbox("Type d'offre", ["Digital product","Ecom (produit physique)"], key="comp_offer")
    brand_type_c = st.radio("Type de marque", ["Nouveau lancement","Marque etablie"], key="comp_brand", horizontal=True)
    market_c     = ""

    run_comp = st.button("⚔️ Lancer la comparaison", type="primary", use_container_width=True, key="comp_run")

    if run_comp:
        if not url_a.strip() or not url_b.strip():
            st.error("Renseignez les deux URLs."); return

        results = {}
        for url, label, col_key in [(url_a, label_a, "A"), (url_b, label_b, "B")]:
            with st.spinner(f"Extraction + audit {label}..."):
                content, status, is_js = extract_page(url.strip())
                if not content:
                    st.error(f"Impossible d'extraire {label} : {status}"); return
                page_type = detect_page_type(content, url.strip())
                page_lang = detect_language(content)
                try:
                    res = run_audit(mode_c, platform_c, offer_type_c, content, "",
                                   market_c, model, brand_type=brand_type_c,
                                   page_type=page_type, page_lang=page_lang)
                    results[col_key] = {"result": res, "label": label, "url": url,
                                        "page_type": page_type}
                except Exception as e:
                    st.error(f"Erreur audit {label} : {e}"); return

        if len(results) == 2:
            st.markdown("---")
            ra = results["A"]["result"].get("_c",{})
            rb = results["B"]["result"].get("_c",{})

            # Banner comparatif
            col_a, col_mid, col_b = st.columns([5,1,5])
            for col, r, info in [(col_a, ra, results["A"]), (col_b, rb, results["B"])]:
                with col:
                    sc = r.get("score",0)
                    risk = r.get("risk","High")
                    sc_hex = "#FF4444" if risk=="High" else "#FF8C00" if risk=="Moderate" else "#22c55e"
                    winner = sc == max(ra.get("score",0), rb.get("score",0))
                    st.markdown(
                        f"""<div style='background:#1a1a2e;border-left:4px solid {sc_hex};
                            border-radius:8px;padding:16px;text-align:center'>
                          {"<div style='color:#FFD700;font-size:0.8em;font-weight:bold'>👑 MEILLEUR SCORE</div>" if winner else ""}
                          <div style='color:#888;font-size:0.8em'>{info['label']}</div>
                          <div style='color:{sc_hex};font-size:2.5em;font-weight:900'>{sc}<span style='font-size:0.4em;color:#555'>/20</span></div>
                          <div style='color:{sc_hex};font-size:0.9em'>{r.get('decision','')}</div>
                        </div>""", unsafe_allow_html=True
                    )
            with col_mid:
                st.markdown("<div style='text-align:center;padding-top:40px;color:#555;font-size:1.5em'>VS</div>", unsafe_allow_html=True)

            # Tableau comparatif détaillé
            st.markdown("---")
            st.subheader("Breakdown comparatif")
            comp_rows = []
            for label, key_a, key_b in [
                ("Hook",     "hook",    "hook"),
                ("Offer",    "offer",   "offer"),
                ("Trust",    "trust",   "trust"),
                ("Friction", "friction","friction"),
                ("Total",    "score",   "score"),
            ]:
                va = ra.get(key_a,0); vb = rb.get(key_b,0)
                mx = 5 if label != "Total" else 20
                winner_a = "✅" if va > vb else ("🤝" if va == vb else "")
                winner_b = "✅" if vb > va else ("🤝" if va == vb else "")
                hxa = _score_color_str(va, mx)
                hxb = _score_color_str(vb, mx)
                comp_rows.append([
                    f"**{label}**",
                    f"{winner_a} **{va}/{mx}**",
                    f"{winner_b} **{vb}/{mx}**",
                ])
            import pandas as pd
            df = pd.DataFrame(comp_rows, columns=["Critère", results["A"]["label"], results["B"]["label"]])
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Résumés
            st.markdown("---")
            ca2, cb2 = st.columns(2)
            with ca2:
                st.markdown(f"#### {results['A']['label']}")
                render_results(results["A"]["result"])
            with cb2:
                st.markdown(f"#### {results['B']['label']}")
                render_results(results["B"]["result"])

def _score_color_str(v, mx=5):
    r = v / mx
    if r <= 0.45: return "#FF4444"
    if r <= 0.65: return "#FF8C00"
    return "#22c55e"

# ── ONBOARDING ───────────────────────────────────────────────
def render_onboarding_banner():
    """
    Affiche un guide de démarrage pour les nouveaux utilisateurs.
    Disparaît une fois que l'utilisateur clique "Compris".
    """
    if st.session_state.get("onboarded"):
        return

    st.markdown(
        """
        <div style='background:linear-gradient(135deg,#1a1a2e,#16213e);
             border:2px solid #6366f1;border-radius:14px;
             padding:24px 28px;margin-bottom:20px'>
          <div style='color:#6366f1;font-size:1.1em;font-weight:700;margin-bottom:8px'>
            👋 Bienvenue sur LRS™ — Launch Risk System
          </div>
          <div style='color:#ccc;font-size:0.92em;line-height:1.7'>
            <b style='color:#fff'>3 étapes pour votre premier audit :</b><br>
            &nbsp;&nbsp;<span style='color:#6366f1'>①</span> &nbsp;Collez l'URL de votre landing page dans l'onglet <b>Audit</b><br>
            &nbsp;&nbsp;<span style='color:#6366f1'>②</span> &nbsp;Choisissez votre plateforme publicitaire et le type d'offre<br>
            &nbsp;&nbsp;<span style='color:#6366f1'>③</span> &nbsp;Cliquez <b>🚀 Run LRS Audit</b> — résultats en 15 secondes<br><br>
            <b style='color:#fff'>Fonctionnalités disponibles :</b>
            &nbsp;Audit · Comparaison · Projets multi-pages · Bulk audit · Monitoring planifié · Export PDF client
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_ok, col_skip = st.columns([1, 5])
    with col_ok:
        if st.button("✅ Compris, démarrer", type="primary", key="onboarding_ok"):
            mark_onboarded()
            st.session_state.onboarded = True
            st.rerun()

# ── ADS LIBRARY ──────────────────────────────────────────────
def _card(title, items, color="#6366f1", icon=""):
    """Render a compact framework card."""
    rows = "".join(
        f"<div style='padding:5px 0;border-bottom:1px solid #1e1e3a;color:#ccc;font-size:0.83em'>{item}</div>"
        for item in items
    )
    st.markdown(
        f"""<div style='background:#0f0f1a;border:1px solid #1e1e3a;
            border-left:3px solid {color};border-radius:8px;padding:14px 16px;margin-bottom:10px'>
          <div style='color:{color};font-weight:700;font-size:0.88em;margin-bottom:8px'>{icon} {title}</div>
          {rows}
        </div>""",
        unsafe_allow_html=True,
    )

def _stat(value, label, color="#6366f1"):
    st.markdown(
        f"""<div style='background:#0f0f1a;border:1px solid #1e1e3a;border-radius:8px;
            padding:14px;text-align:center;margin-bottom:8px'>
          <div style='color:{color};font-size:1.8em;font-weight:800;line-height:1'>{value}</div>
          <div style='color:#666;font-size:0.75em;margin-top:4px'>{label}</div>
        </div>""",
        unsafe_allow_html=True,
    )

def render_ads_library():
    st.markdown(
        """<div style='background:linear-gradient(135deg,#1a1a2e,#0f0f1a);
            border:1px solid #2a2a4a;border-radius:10px;padding:18px 22px;margin-bottom:18px'>
          <div style='color:#fff;font-size:1.1rem;font-weight:800'>📚 Ads Library — LRS™</div>
          <div style='color:#666;font-size:0.83em;margin-top:4px'>
            Frameworks, templates et guides opérationnels par plateforme.
            Utilisez ces ressources pour construire des campagnes avant de lancer votre audit.
          </div>
        </div>""",
        unsafe_allow_html=True,
    )

    tab_meta, tab_tik, tab_ggl, tab_funnel, tab_copy = st.tabs([
        "📘 Meta Ads", "🎵 TikTok Ads", "🔍 Google Ads", "🛒 Funnel Écom", "✍️ Copywriting"
    ])

    # ── META ADS ──────────────────────────────────────────────
    with tab_meta:
        st.markdown("#### Frameworks rapides")
        col1, col2 = st.columns(2)
        with col1:
            _card("Hook Formula — 4 types", [
                "❓ Question : 'Pourquoi vos pubs Meta ne convertissent pas?'",
                "📊 Stat choc : '73% des campagnes échouent dès J1 — voici pourquoi'",
                "🛑 Pattern interrupt : visuel inattendu + texte court",
                "👤 Identification : 'Si tu fais du paid traffic...'",
            ], color="#6366f1", icon="🎯")
            _card("Structure pub Meta", [
                "0–3s : Hook visuel + texte overlay (une phrase max)",
                "3–15s : Corps — problème → solution → preuve",
                "15–30s : CTA clair + urgence ('Offre se termine dimanche')",
                "Primary text : 125 car. avant 'Voir plus' → hook obligatoire",
            ], color="#22c55e", icon="📐")
        with col2:
            _card("Benchmarks CTR (cold traffic)", [
                "✅ > 2% CTR : bon — publiez davantage",
                "🚀 > 4% CTR : excellent — scalez le budget",
                "⚠️  < 1% CTR : créa à revoir ou audience trop large",
                "CPM acceptable : 8–18€ (FR, ecom/digital)",
                "Fréquence > 3.5 : creative fatigue, changez la créa",
            ], color="#FF8C00", icon="📊")
            _card("Modèles de primary text", [
                "PAS : Problème → Agitate ('tu perds X€/j') → Solve",
                "Social Proof : '[Prénom] a obtenu [résultat] en [durée]'",
                "Direct : '[Bénéfice] sans [douleur] — voici comment'",
                "Question + Réponse : 'Tu veux X? Voilà ce que font les pros'",
            ], color="#06b6d4", icon="✍️")

        st.markdown("---")
        st.markdown("#### Guide complet Meta Ads")

        with st.expander("🎯 Stratégie d'audiences — de zéro à scale"):
            st.markdown("""
**Phase 1 — Testing cold traffic**
- Broad (sans intérêts) sur comportements d'achat larges — budget 20€/j par adset
- Lookalike 1-3% sur vos meilleurs acheteurs (LAL)
- 1-2 intérêts larges très ciblés (pas les intérêts évidents)

**Phase 2 — Scale ce qui marche**
- ROAS > 2.5 → doublez le budget tous les 3 jours max (pas tous les jours)
- CBO (Campaign Budget Optimization) une fois que vous avez 2+ adsets gagnants
- Évitez de toucher une adset active les 3 premiers jours — laissez l'algo apprendre

**Phase 3 — Retargeting**
- Visiteurs 7j non-acheteurs : montrez les preuves sociales (reviews, résultats)
- ATC 14j non-acheteurs : urgence + offre légèrement différente
- Acheteurs 180j : upsell / cross-sell — CPM ultra-bas, ROAS élevé
""")

        with st.expander("📐 Formats créatifs gagnants en 2025"):
            st.markdown("""
**Image statique avec texte overlay** (fonctionne toujours)
- Fond simple ou produit seul — texte blanc sur fond sombre
- La règle : 1 image = 1 message = 1 CTA
- Ratio 1:1 pour Feed, 9:16 pour Stories/Reels

**UGC 15–30s** (meilleur ROAS actuellement)
- Personne réelle face caméra, son naturel, tenu décontractée
- Structure : pain point 0-3s → solution → démonstration → résultat
- Pas de musique de fond, pas de logo au début — must feel native

**Reels natifs avec voiceover**
- Tendances visuelles TikTok adaptées à Meta
- Hook textuel sur les 2 premières secondes
- Sous-titres obligatoires (85% regardent sans son)

**Carousel ecom**
- Slide 1 : bénéfice principal (pas le produit)
- Slides 2-4 : preuves, features, résultats
- Slide finale : CTA + offre
""")

        with st.expander("⚙️ Structure de compte optimale"):
            st.markdown("""
**Structure recommandée 2025 :**
```
Campagne CBO — [Objectif : Ventes]
  ├── Adset 1 : Broad 18-45 (pas d'intérêts)
  ├── Adset 2 : LAL 1-3% acheteurs
  └── Adset 3 : Intérêt large #1
      ├── Créa A (image statique)
      ├── Créa B (UGC 15s)
      └── Créa C (Reels natif)
```

**Règles d'or :**
- 1 campagne Prospection + 1 campagne Retargeting (séparées !)
- Minimum 3 créas par adset pour donner de l'espace à l'algo
- Ne changez pas le budget de + 20% en une seule fois — reset la phase d'apprentissage
- Pixel : Event Purchase obligatoire avant de lancer (conversion event)
""")

    # ── TIKTOK ADS ────────────────────────────────────────────
    with tab_tik:
        st.markdown("#### Frameworks rapides")
        col1, col2 = st.columns(2)
        with col1:
            _card("La règle des 2 premières secondes", [
                "Le scroll dure 0.5s — votre hook doit arrêter le pouce",
                "✅ Visuel inattendu OU texte choc en overlay immédiat",
                "✅ Commencer IN MEDIAS RES (milieu d'action)",
                "❌ Logo au début = skip garanti",
                "❌ Intro lente avec musique = perte d'audience",
            ], color="#FF0050", icon="⚡")
            _card("Structure vidéo TikTok Ads", [
                "0-2s : Hook visuel + texte (pattern interrupt)",
                "2-8s : Problème ou identification ('Si tu fais X...')",
                "8-18s : Solution + démonstration rapide",
                "18-25s : Preuve sociale (before/after, témoignage)",
                "25-30s : CTA clair + urgence",
            ], color="#FF0050", icon="📱")
        with col2:
            _card("Benchmarks TikTok Ads", [
                "✅ CTR > 2.5% : bon pour cold traffic",
                "✅ CPM : 5–12€ (FR) — plus bas que Meta",
                "⚠️  VTR (View-Through Rate) > 25% à 6s : hook OK",
                "🚀 ROAS > 2.0 avant de scale",
                "Fréquence > 2.5 en 7j : nouvelle créa urgente",
            ], color="#22c55e", icon="📊")
            _card("Formats natifs gagnants", [
                "UGC face caméra : 15–30s, son naturel ambiant",
                "Spark Ads : boostez vos contenus organiques TikTok",
                "Trending audio : utilisez les sons tendance dans les 48h",
                "Text-overlay : sous-titres auto OU manuels stylisés",
                "Duet / Reaction : réaction au produit en temps réel",
            ], color="#06b6d4", icon="🎬")

        st.markdown("---")
        st.markdown("#### Guide complet TikTok Ads")

        with st.expander("🎬 Créer des hooks qui stoppent le scroll"):
            st.markdown("""
**Les 5 types de hooks qui convertissent :**

1. **La question directe** : "Tu sais pourquoi ton ROAS chute chaque mois?"
2. **Le résultat choquant** : "J'ai fait 12 000€ en 4 jours avec une pub de 300€"
3. **Le contre-intuitif** : "Stop de cibler tes concurrents sur Meta — voici pourquoi"
4. **L'identification** : "Ce problème concerne TOUS les e-commerçants en 2025"
5. **Le teaser** : "Je vais te montrer exactement comment j'ai fait... regarde jusqu'à la fin"

**Erreurs communes :**
- Texte overlay trop long (max 6 mots en hook)
- Visage hors cadre ou mal éclairé
- Audio de mauvaise qualité (deal breaker sur TikTok)
- CTA vague ("cliquez ici") → soyez précis ("Lien en bio — offre 48h")
""")

        with st.expander("⚙️ Setup campagne TikTok Ads (structure 2025)"):
            st.markdown("""
**Budget minimum :** 30–50€/jour pour que l'algo apprenne correctement.

**Structure recommandée :**
```
Campagne — [Objectif : Conversions / Achat]
  ├── Adset 1 : Broad (18-35, FR) — pas d'intérêts
  ├── Adset 2 : Custom Audience (visiteurs 30j)
  └── Adset 3 : Lookalike 1-5% acheteurs
      ├── Créa 1 (UGC 15s)
      ├── Créa 2 (Texte overlay + produit)
      └── Créa 3 (Témoignage 20s)
```

**Spark Ads vs. non-Spark :**
- Spark Ads (boost d'un post organique) = meilleure crédibilité sociale, commentaires visibles
- Non-Spark = contrôle total, idéal pour tester des angles sans compromettre votre compte organique
- Recommandation : testez les 2 et comparez le CTR

**Pixel TikTok :** Installez le pixel TikTok ET l'API Conversions (server-side) pour contourner les adblockers — impact +15-25% sur les données remontées.
""")

        with st.expander("🔄 Rythme de testing créatif"):
            st.markdown("""
**Règle d'or TikTok :** Les créas se fatiguent 3x plus vite que sur Meta.

**Cycle recommandé :**
- Semaine 1-2 : testez 3-5 créas, budget 30-50€/j par adset
- J3 : regardez le VTR à 6s. < 20% = hook raté, coupez la créa
- J5 : regardez le CTR et le CPA. > objectif = scalez le budget x1.5
- Semaine 3 : créez 2-3 variations des créas gagnantes (même angle, format différent)
- Semaine 4+ : nouvelles créas sur nouveaux angles si le ROAS baisse

**Rotation créative :** 1 nouvelle créa par semaine minimum pour maintenir les performances.
""")

    # ── GOOGLE ADS ────────────────────────────────────────────
    with tab_ggl:
        st.markdown("#### Frameworks rapides")
        col1, col2 = st.columns(2)
        with col1:
            _card("Structure d'annonce Search RSA", [
                "Headline 1 (30 car.) : mot clé principal exact",
                "Headline 2 (30 car.) : bénéfice principal + chiffre",
                "Headline 3 (30 car.) : CTA ou urgence ('Dès 47€')",
                "Description 1 (90 car.) : USP principale + preuve",
                "Description 2 (90 car.) : objection principale + garantie",
            ], color="#4285F4", icon="🔍")
            _card("Extensions indispensables", [
                "Sitelinks : 4 liens vers pages clés (FAQ, Prix, Témoignages...)",
                "Callouts : USP courtes ('Livraison 24h', 'Garantie 30j')",
                "Structured snippets : liste de produits/services",
                "Call extension : numéro visible (B2B++)",
                "Price extension : vos offres avec prix visible",
            ], color="#4285F4", icon="🔧")
        with col2:
            _card("Types de correspondance", [
                "[Exact] : contrôle maximum, volume faible",
                "\"Expression\" : équilibre volume / pertinence",
                "Large : volume élevé, nécessite liste de mots exclus",
                "→ Commencez en Exact, élargissez quand CPA OK",
                "→ Liste de négatifs : mots hors-cible à exclure dès J1",
            ], color="#34A853", icon="🎯")
            _card("Quality Score — les 3 piliers", [
                "1. Pertinence annonce (mot clé dans headline = +QS)",
                "2. CTR attendu vs concurrents (créa = différenciation)",
                "3. Expérience landing page (LRS vous aide ici 🚦)",
                "QS 7-10 : CPC réduit jusqu'à 50% vs. QS < 5",
                "LP lente (> 3s) = QS pénalisé — optimisez le Core Web Vitals",
            ], color="#FBBC05", icon="⭐")

        st.markdown("---")
        st.markdown("#### Guide complet Google Ads")

        with st.expander("🏗️ Structure de compte recommandée"):
            st.markdown("""
**Principe SKAG vs. thématique (2025) :**
Les SKAGs (1 mot clé par adset) sont dépassés. Google favorise les RSA et le broad match intelligent.

**Structure thématique recommandée :**
```
Compte
  ├── Campagne Search — [Produit Principal]
  │     ├── Adgroup : mots clés achat ("acheter X", "prix X", "commander X")
  │     ├── Adgroup : mots clés comparaison ("X vs Y", "meilleur X")
  │     └── Adgroup : mots clés problème ("comment [résoudre problème]")
  │
  ├── Campagne Shopping — [Flux produit optimisé]
  │
  └── Campagne Retargeting — [RLSA + Display]
```

**Budget testing :** 20€/j minimum par campagne Search pour que l'algo ait assez de données en 7-14 jours.
""")

        with st.expander("📈 Stratégies d'enchères — quand utiliser quoi"):
            st.markdown("""
| Stratégie | Quand l'utiliser |
|-----------|-----------------|
| Maximiser les clics | Lancement, objectif = données |
| Maximiser les conversions | Après 30+ conversions/mois |
| CPA cible | Budget stable + historique conversions fiable |
| ROAS cible | E-com avec valeurs paniers variables |
| CPM cible | Display/YouTube — notoriété uniquement |

**Règle :** Ne changez jamais la stratégie d'enchères les 2 premières semaines. L'algo a besoin de 7-14 jours pour apprendre.

**Performance Max :** Évitez en cold traffic pur — PMax cannibalisera vos campagnes Search. Activez-le une fois que Search fonctionne et que vous avez des données de conversion.
""")

        with st.expander("🛒 Google Shopping — optimiser son flux"):
            st.markdown("""
**Les 3 éléments qui font 80% du succès Shopping :**

1. **Titre produit** (le plus important) :
   - Format : `[Marque] [Type produit] [Attribut principal] [Taille/Couleur/Variante]`
   - Exemple : "Nike Air Max 90 Blanc Homme 42 — Chaussures Running"
   - Le mot clé doit être dans les 70 premiers caractères

2. **Image produit** :
   - Fond blanc ou transparent — pas de lifestyle pour Shopping
   - Produit bien centré, occupe > 75% du cadre
   - PNG haute résolution (min. 800x800)

3. **Prix** :
   - Prix barré (prix_comparaison) très visible améliore le CTR
   - Frais de port clairement affichés (ou 'Livraison gratuite')
   - Promotions Merchant Center = badge "Promotion" sur l'annonce

**Segmentation des enchères :** Créez des groupes de produits séparés pour vos bestsellers (enchère haute) vs. catalogue complet (enchère basse).
""")

    # ── FUNNEL ÉCOM ───────────────────────────────────────────
    with tab_funnel:
        st.markdown("#### Structures de funnels")
        col1, col2, col3 = st.columns(3)
        with col1:
            _card("Funnel Direct Response", [
                "Ad → Landing Page courte → Checkout",
                "⚡ Le plus simple, idéal pour tester",
                "LP : 500-800 mots, 1 CTA, pas de nav",
                "Checkout : 1-page, confiance++",
                "Upsell : bump offer sur checkout",
            ], color="#6366f1", icon="🎯")
        with col2:
            _card("Funnel VSL (Video Sales Letter)", [
                "Ad → LP avec vidéo → Checkout → Upsells",
                "📹 VSL 8-20 min pour produits 97€+",
                "Vidéo autoplay sans controls (dès possible)",
                "CTA apparaît à 60% de la vidéo",
                "Upsell 1 (complémentaire) + Upsell 2 (premium)",
            ], color="#22c55e", icon="🎬")
        with col3:
            _card("Funnel Lead Magnet", [
                "Ad → Optin (email) → Email nurturing → Vente",
                "🎁 Idéal : info-produit, coaching, SaaS",
                "Lead magnet : valeur perçue élevée, résultat rapide",
                "Sequence 5 emails : valeur → valeur → pitch → urgence → dernière chance",
                "Retargeting parallèle sur les optins non-convertis",
            ], color="#FF8C00", icon="📧")

        st.markdown("---")
        st.markdown("#### Les règles immuables d'une landing page qui convertit")

        col_a, col_b = st.columns(2)
        with col_a:
            _card("Structure LP haute conversion", [
                "① Hero : headline + sous-titre + CTA above the fold",
                "② Problème : 'Vous aussi vous souffrez de...'",
                "③ Solution : votre produit = le pont",
                "④ Preuves : before/after, témoignages, chiffres",
                "⑤ Offre : ce que vous obtenez (offer stack)",
                "⑥ Garantie : réduction du risque perçu",
                "⑦ CTA final : urgence + bouton",
            ], color="#6366f1", icon="📄")
            _card("Les erreurs qui tuent la conversion", [
                "❌ Navigation header visible (fuite = -20-40% CVR)",
                "❌ CTA générique ('En savoir plus', 'Cliquer ici')",
                "❌ Prix sans contexte (pas de comparaison / barré)",
                "❌ Garantie absente ou invisible",
                "❌ Pas de preuve sociale above the fold",
                "❌ Page trop lente > 3s (Google = -53% de taux de rebond)",
            ], color="#FF4444", icon="⚠️")
        with col_b:
            _card("Offer Stack — comment présenter l'offre", [
                "Listez TOUT ce que le client obtient avec valeur €",
                "Produit principal : 'Valeur : 197€'",
                "Bonus 1 : 'Valeur : 97€' (doit sembler plus cher que le prix)",
                "Bonus 2 : 'Valeur : 47€'",
                "Garantie 30j : 'Risque zéro'",
                "Prix total barré → 'Aujourd'hui seulement : 47€'",
            ], color="#22c55e", icon="🎁")
            _card("Optimisation du checkout", [
                "1-page checkout = meilleur CVR (Shopify, ThriveCart...)",
                "Bump offer visible (+15-25% revenu moyen)",
                "Logos de paiement sécurisé sous le bouton",
                "Résumé commande visible à droite du formulaire",
                "Testimonial ou stat sous le CTA checkout",
            ], color="#FF8C00", icon="🛒")

        with st.expander("📊 Benchmarks CVR par type de page"):
            st.markdown("""
| Type de page | CVR faible | CVR moyen | CVR excellent |
|---|---|---|---|
| Landing page cold traffic | < 1% | 1.5–3% | > 4% |
| Page produit ecom | < 1.5% | 2–4% | > 5% |
| Checkout (visiteurs LP) | < 30% | 40–60% | > 70% |
| Optin page (lead magnet) | < 20% | 30–50% | > 60% |
| Upsell 1 | < 10% | 15–25% | > 35% |

*Ces benchmarks varient selon le prix, la niche et la source de trafic. Utilisez LRS pour identifier ce qui plombe votre CVR.*
""")

    # ── COPYWRITING ───────────────────────────────────────────
    with tab_copy:
        st.markdown("#### Frameworks de copywriting")
        col1, col2 = st.columns(2)
        with col1:
            _card("PAS — Problem · Agitate · Solve", [
                "P : Nommez le problème EXACTEMENT comme le client le ressent",
                "A : Agitez — 'Et ça coûte X€ par mois / détruit votre...'",
                "S : Présentez votre solution comme l'évidence",
                "⚡ Idéal pour : primary text, email, VSL intro",
            ], color="#6366f1", icon="🔥")
            _card("AIDA — Attention · Interest · Desire · Action", [
                "A : Attention — hook fort (stat, question, choc)",
                "I : Interest — pourquoi c'est pertinent POUR EUX",
                "D : Desire — bénéfices concrets + preuves",
                "A : Action — CTA clair + urgence",
                "⚡ Idéal pour : landing page, email séquence",
            ], color="#22c55e", icon="📈")
            _card("BAB — Before · After · Bridge", [
                "Before : 'Avant, tu passais 2h à optimiser tes pubs...'",
                "After : 'Imagine avoir le score exact avant de dépenser 1€'",
                "Bridge : 'C'est exactement ce que fait LRS™ en 15s'",
                "⚡ Idéal pour : témoignages, ads UGC, email welcome",
            ], color="#FF8C00", icon="🌉")
        with col2:
            _card("Les 4U — Urgent · Unique · Utile · Ultra-spécifique", [
                "Urgent : pourquoi agir maintenant? (prix, stock, délai)",
                "Unique : qu'est-ce que VOUS avez que personne d'autre n'a?",
                "Utile : quel résultat concret et mesurable?",
                "Ultra-spécifique : '23% de CVR en 7 jours' > 'plus de ventes'",
                "⚡ Checklist pour chaque headline que vous écrivez",
            ], color="#06b6d4", icon="✅")
            _card("Formules d'hooks éprouvées", [
                "'[Chiffre] [persona] ont [résultat] en [durée]'",
                "'La vraie raison pourquoi [problème persiste]'",
                "'Stop [action commune] — voici ce qui marche vraiment'",
                "'Comment [résultat désiré] sans [douleur habituelle]'",
                "'Ce que [autorité] ne veut pas que vous sachiez sur [sujet]'",
            ], color="#FF4444", icon="💡")

        st.markdown("---")
        st.markdown("#### Templates prêts à l'emploi")

        with st.expander("📝 Templates primary text Meta Ads (copy-paste)"):
            st.markdown("""
**Template PAS (30-60 mots) :**
```
Tu dépenses 500€/mois en pubs Meta et tu te demandes pourquoi ton ROAS plafonne à 1.2?

La vraie raison : ta landing page ne convertit pas le trafic que tu envoies dessus.

[Nom produit] analyse ta LP en 15 secondes et te dit exactement ce qui bloque les conversions.

👉 Teste gratuitement → [Lien]
```

**Template Social Proof (40-70 mots) :**
```
"J'ai passé 3 mois à tester des pubs sans comprendre pourquoi ça ne scalait pas.

LRS m'a dit en 15 secondes que mon hook était à 2/5. J'ai changé la headline.

La semaine suivante : ROAS 3.8 au lieu de 1.4."

— [Prénom], e-commerçant (niche X)

→ Découvrez votre score LRS : [Lien]
```

**Template Direct Response (20-40 mots) :**
```
Votre landing page est prête pour le paid traffic?

Score /20 · Plan d'action · Rewrites générés en 15 secondes.

Utilisé par [X] media buyers en France.

Testez maintenant → [Lien]
```
""")

        with st.expander("🎯 Comment écrire une headline qui convertit"):
            st.markdown("""
**Les 3 composantes d'une headline parfaite :**

1. **Bénéfice spécifique** (pas une feature) + **timeframe** + **sans douleur**
   - ❌ "Améliorez vos pubs avec notre outil IA"
   - ✅ "Doublez votre ROAS en 7 jours sans changer votre budget pub"

2. **Intégrez un chiffre** — les chiffres spécifiques sont +28% plus mémorisables
   - ❌ "Économisez du temps sur vos audits"
   - ✅ "Auditez votre landing page en 15 secondes chrono"

3. **Adressez le sceptique** — anticipez l'objection #1
   - ❌ "L'outil qui révolutionne le paid traffic"
   - ✅ "Le premier outil d'audit paid traffic qui vous dit exactement QUOI corriger"

**Test rapide :** Si votre headline peut s'appliquer à n'importe quel concurrent, elle est trop générique. Retravaillez-la.
""")

        with st.expander("⚡ Rédiger un CTA qui convertit"):
            st.markdown("""
**Règle : le CTA doit être une continuation logique de la promesse**

| ❌ CTA générique | ✅ CTA spécifique |
|---|---|
| "Acheter maintenant" | "Obtenir mon score /20 →" |
| "En savoir plus" | "Voir comment doubler mon ROAS" |
| "S'inscrire" | "Démarrer mon audit gratuit" |
| "Cliquer ici" | "Analyser ma landing page maintenant" |

**Ajouter de l'urgence crédible :**
- Temps limité : "Offre valable jusqu'au [date proche]"
- Stock limité : "Accès limité à 50 utilisateurs ce mois"
- Bonus expirant : "Bonus offert si vous rejoignez avant minuit"

⚠️ L'urgence inventée détruit la confiance. N'utilisez que ce qui est réel et vérifiable.
""")


# ── CHANGELOG ────────────────────────────────────────────────
def render_changelog():
    st.subheader("📋 Changelog LRS™")
    st.caption("Historique de toutes les améliorations apportées à l'outil.")

    versions = [
        ("V2.6 — Aujourd'hui", [
            "🆕 Bulk Audit : auditez jusqu'à 20 URLs en 1 clic + import CSV + export résultats CSV",
            "🆕 Monitoring : alertes score (drop/progression ≥2 pts), score trend par page",
            "🆕 Audits planifiés automatiques : surveillance toutes les 7/14/30 jours, exécution au démarrage",
            "🆕 Onboarding interactif : guide de démarrage pour les nouveaux utilisateurs",
            "🆕 Onglet Monitoring avec podium, tableau comparatif et badge d'alerte",
        ]),
        ("V2.5", [
            "🆕 Profils d'audit sauvegardés (charger / sauvegarder vos paramètres habituels)",
            "🆕 Delta de score : progression globale depuis le premier audit visible dans l'Historique",
            "🆕 Tracker d'implémentation des recommandations (checkboxes + barre de progression)",
            "🆕 Bouton Re-audit : URL pré-remplie automatiquement depuis l'Historique",
            "🆕 Projets multi-pages : groupez un funnel complet et auditez tout en 1 clic",
            "🆕 Rapport Client PDF : export branding client avec nom du destinataire",
        ]),
        ("V2.4", [
            "🆕 Export rapport PDF professionnel (branding LRS, fond sombre, 4 pages)",
            "🆕 Mode Comparaison : auditer 2 URLs côte à côte",
            "🆕 Mode Avant/Après : comparer un audit avec un précédent",
            "🆕 Changelog intégré dans l'app",
            "🆕 Benchmark Report 2025 (PDF téléchargeable — valeur €27-47)",
        ]),
        ("V2.3", [
            "🆕 Historique persistant (JSON) — survit au refresh de page",
            "🆕 Warning pages JavaScript / contenu insuffisant",
            "🆕 Jauge visuelle du score (bandeau coloré rouge/orange/vert)",
            "🆕 Few-shot examples dans le prompt — scoring plus cohérent",
            "🆕 Retry automatique OpenAI (3 tentatives avec backoff)",
            "🆕 Détection langue de la page (FR / EN / Mixte)",
        ]),
        ("V2.2", [
            "🔧 Fix détection page produit (/products/ classé en Catalogue → corrigé)",
            "🆕 Scoring adaptatif par type de page (fiche produit ≠ landing page)",
            "🆕 Aperçu du contenu scrapé (debug)",
            "🆕 Priorité above-the-fold dans le scraping",
            "🆕 Graphique d'évolution des scores dans Historique",
            "🔧 User-Agent amélioré pour meilleure compatibilité",
        ]),
        ("V2.1", [
            "🔧 Bug 1 : Scoring trop sévère pour marques établies → sélecteur Marque établie / Nouveau lancement",
            "🔧 Bug 2 : Auto-détection du type de page (Sales, Catalogue, SaaS, Blog, Lead Gen)",
            "🔧 Bug 3 : Recommandations granulaires — Quick Wins, Long Terme, Action Prioritaire #1 avec how_exactly",
            "🆕 max_tokens augmenté à 4500",
        ]),
        ("V2.0 — Version initiale", [
            "✅ Audit Funnel Only / Ads Only / Full Risk",
            "✅ Scoring Hook/Offer/Trust/Friction sur 20",
            "✅ Contexte marché personnalisé",
            "✅ Plan d'action, Rewrite, Ad Creative",
            "✅ Export .txt",
            "✅ Checklist pré-lancement",
            "✅ Historique de session",
            "✅ Gate accès par mot de passe",
            "✅ Deploy Streamlit Cloud",
        ]),
    ]

    for v_title, items in versions:
        with st.expander(v_title, expanded=(v_title.startswith("V2.6"))):
            for item in items:
                st.markdown(item)

# ── MAIN ─────────────────────────────────────────────────────
# ── CONTROLE D'ACCES PAR MOT DE PASSE ───────────────────────
# ── BENCHMARK REPORT TAB ─────────────────────────────────────
def render_benchmark_tab():
    st.subheader("📊 Rapport Benchmark — État des Landing Pages 2025")

    col_a, col_b = st.columns([3, 2])
    with col_a:
        st.markdown("""
**Ce que contient le rapport (27 pages) :**
- Scores moyens par niche (Ecom, SaaS, Lead Gen, Coaching…)
- Top 10 erreurs de landing pages et comment les corriger
- Anatomie d'une page parfaite (18+/20 LRS Score)
- 6 Quick Wins applicables en moins d'1h
- Benchmarks CVR par secteur
- Top 5 hooks qui convertissent en 2025
- Roadmap 30 jours pour passer de 10→18/20
        """)

    with col_b:
        st.markdown("#### 🎁 Inclus avec votre accès LRS™")
        st.markdown("Valeur standalone : **€27–47**")

        # Charger le PDF depuis le fichier
        benchmark_path = os.path.join(os.path.dirname(__file__), "LRS_Benchmark_Report_2025.pdf")
        try:
            with open(benchmark_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                label="⬇️ Télécharger le Rapport PDF",
                data=pdf_bytes,
                file_name="LRS_Benchmark_Report_2025.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True,
            )
            st.caption(f"PDF · {len(pdf_bytes) // 1024} Ko · Mis à jour Avril 2025")
        except FileNotFoundError:
            # Regénérer à la volée si fichier absent
            try:
                from generate_benchmark_report import generate as gen_benchmark
                pdf_bytes = gen_benchmark()
                st.download_button(
                    label="⬇️ Télécharger le Rapport PDF",
                    data=pdf_bytes,
                    file_name="LRS_Benchmark_Report_2025.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"Rapport temporairement indisponible : {e}")

    st.markdown("---")
    st.markdown("#### 📌 Extraits du rapport")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Score moyen Ecom", "11.2 / 20", "-1.8 vs SaaS")
        st.caption("Basé sur 200+ audits LRS")
    with col2:
        st.metric("Erreur #1", "Hook générique", "présente dans 78% des pages")
        st.caption("Fix : promesse spécifique + chiffre")
    with col3:
        st.metric("Uplift CVR moyen", "+2.1 pts", "après quick wins")
        st.caption("Sur pages auditées LRS ≥ 12/20")

    st.markdown("---")
    st.info(
        "💡 **Astuce** : Lancez un audit LRS sur votre page, puis comparez votre score "
        "aux benchmarks du rapport pour identifier vos priorités immédiates."
    )


def check_access():
    """
    Verifie le mot de passe d'acces.
    - Si APP_PASSWORD n'est pas defini → acces libre (mode dev local)
    - Si APP_PASSWORD est defini → mot de passe requis (mode production)
    Pour definir le mot de passe :
      Local : APP_PASSWORD=mon-mdp dans .env
      Streamlit Cloud : APP_PASSWORD = "mon-mdp" dans Secrets
    """
    pwd_required = os.getenv("APP_PASSWORD", "")
    if not pwd_required:
        try:
            pwd_required = st.secrets.get("APP_PASSWORD", "")
        except Exception:
            pass

    if not pwd_required:
        return True  # Pas de mot de passe configure = acces libre (dev)

    if st.session_state.get("authenticated"):
        return True

    st.markdown("# 🚦 LRS™ — Launch Risk System")
    st.markdown("### Enter your access password")
    st.markdown("Don't have access yet? [Get LRS™ access](#)")  # remplace # par ton lien Lemon Squeezy

    entered = st.text_input("Password", type="password", placeholder="Enter your password...")
    if st.button("Access LRS →", type="primary"):
        if entered == pwd_required:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Invalid password. Purchase your access to get your password.")
    return False


def main():
    init_session()
    light_mode = st.session_state.get("light_mode", False)
    inject_css(light_mode=light_mode)

    if not check_access():
        st.stop()

    # ── Header ───────────────────────────────────────────────
    hdr_l, hdr_r = st.columns([5, 1])
    border_col = "#dde0ef" if light_mode else "#1e1e3a"
    txt_col    = "#1a1a2e" if light_mode else "#fff"
    sub_col    = "#888"    if light_mode else "#555"
    tag_col    = "#aaa"    if light_mode else "#444"
    with hdr_l:
        st.markdown(
            f"""<div style='display:flex;align-items:center;
                margin-bottom:1.2rem;padding-bottom:0.8rem;border-bottom:1px solid {border_col}'>
              <div>
                <span style='font-size:1.6rem;font-weight:800;color:{txt_col};letter-spacing:-0.5px'>
                  🚦 LRS™
                </span>
                <span style='color:{sub_col};font-size:0.85rem;margin-left:10px'>
                  Launch Risk System · V{APP_VERSION}
                </span>
              </div>
              <span style='color:{tag_col};font-size:0.78rem;margin-left:auto'>Paid Traffic Pre-Launch Audit</span>
            </div>""",
            unsafe_allow_html=True,
        )
    with hdr_r:
        toggle_label = "☀️ Light" if not light_mode else "🌙 Dark"
        if st.button(toggle_label, key="theme_toggle", help="Basculer mode clair/sombre"):
            st.session_state.light_mode = not light_mode
            st.rerun()

    # ── API Key check ────────────────────────────────────────
    api_key = get_api_key()
    if not api_key:
        st.markdown(
            """<div style='background:#1a0a0a;border:1px solid #FF4444;border-radius:10px;
                padding:20px 24px;margin:8px 0'>
              <div style='color:#FF4444;font-weight:700;margin-bottom:6px'>
                🔑 Clé API OpenAI manquante
              </div>
              <div style='color:#ccc;font-size:0.88rem'>
                Ajoutez <code>OPENAI_API_KEY = "sk-..."</code> dans vos
                <strong>Streamlit Secrets</strong> (App settings → Secrets)
                ou dans votre fichier <code>.env</code> en local.
              </div>
            </div>""",
            unsafe_allow_html=True,
        )
        st.stop()

    # ── Scheduler au démarrage ────────────────────────────────
    if not st.session_state.get("scheduled_ran"):
        run_scheduled_audits()
        st.session_state.scheduled_ran = True

    # ── Onboarding ────────────────────────────────────────────
    render_onboarding_banner()

    # ── Calcul alertes (pour badge onglet) ───────────────────
    alerts     = compute_score_alerts(st.session_state.audit_history)
    n_alerts   = len(alerts)
    suivi_label = f"Suivi 🔴" if n_alerts > 0 else "Suivi"

    # ── 5 onglets ────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Audit", "Multi-Audit", suivi_label, "Historique", "Ressources"
    ])

    with tab1:
        col_l, col_r = st.columns([1, 2])

        with col_l:
            # ── Profils ───────────────────────────────────────
            profiles      = st.session_state.profiles
            profile_names = list(profiles.keys())
            if profile_names:
                pc1, pc2 = st.columns([4, 1])
                with pc1:
                    sel_profile = st.selectbox("📂 Profil", ["— Nouveau —"] + profile_names, key="sel_profile", label_visibility="collapsed")
                with pc2:
                    if sel_profile != "— Nouveau —" and st.button("🗑️", key="del_prof", help="Supprimer ce profil"):
                        delete_profile(sel_profile)
                        st.session_state.profiles = load_profiles()
                        st.rerun()
                loaded_prof = profiles.get(sel_profile, {}) if sel_profile != "— Nouveau —" else {}
            else:
                loaded_prof = {}

            def pval(key, default):
                return loaded_prof.get(key, default)

            # ── Champs essentiels ─────────────────────────────
            default_url = st.session_state.get("reaudit_url", "")
            if default_url:
                st.info("🔁 URL pré-remplie depuis l'historique")

            mode = st.selectbox("Mode",
                ["Funnel Only", "Ads Only", "Full Risk"],
                index=["Funnel Only","Ads Only","Full Risk"].index(pval("mode","Funnel Only")),
                help="Funnel Only = audit landing page · Ads Only = audit pub · Full Risk = les deux")

            landing_url = ""
            if mode in ("Funnel Only", "Full Risk"):
                landing_url = st.text_input("URL de la page", value=default_url,
                                             placeholder="https://ma-landing.com")

            ad_text = ""
            if mode in ("Ads Only", "Full Risk"):
                ad_text = st.text_area("Texte de la pub", placeholder="Primary text, headline, script UGC...", height=110)

            r1, r2 = st.columns(2)
            with r1:
                platform = st.selectbox("Plateforme",
                    ["Meta", "TikTok", "Google", "Mixed", "N/A"],
                    index=["Meta","TikTok","Google","Mixed","N/A"].index(pval("platform","Meta")))
            with r2:
                offer_type = st.selectbox("Offre",
                    ["Digital product", "Ecom (produit physique)"],
                    index=["Digital product","Ecom (produit physique)"].index(pval("offer_type","Digital product")))

            bt_opts   = ["Nouveau lancement", "Marque etablie"]
            bt_idx    = bt_opts.index(pval("brand_type","Nouveau lancement")) if pval("brand_type","Nouveau lancement") in bt_opts else 0
            brand_type = st.radio("Type de marque", bt_opts, index=bt_idx, horizontal=True,
                                   help="Marque etablie = Gymshark, Nike… Trust évalué différemment")

            # ── Options avancées (masquées par défaut) ────────
            with st.expander("⚙️ Options avancées"):
                model = st.selectbox("Modèle OpenAI", ["gpt-4o-mini", "gpt-4o"],
                    help="gpt-4o-mini : rapide ~0.01$/audit · gpt-4o : plus précis ~0.10$/audit")
                st.markdown("**Contexte marché** *(améliore la précision)*")
                price       = st.text_input("Prix",        value=pval("price",""),       placeholder="Ex: 47€")
                target      = st.text_input("Cible",       value=pval("target",""),      placeholder="Ex: femmes 25-40, douleurs dos")
                test_budget = st.text_input("Budget test", value=pval("budget",""),      placeholder="Ex: 300€/semaine")
                niche       = st.text_input("Niche",       value=pval("niche",""),       placeholder="Ex: wellness, coaching")
                competitors = st.text_input("Concurrents", value=pval("competitors",""), placeholder="Ex: Calm, Headspace")
                st.markdown("---")
                new_prof_name = st.text_input("Sauvegarder comme profil", placeholder="Nom du profil", key="save_prof_name")
                if st.button("💾 Sauvegarder", key="btn_save_prof"):
                    if new_prof_name.strip():
                        save_profile(new_prof_name.strip(), {
                            "mode": mode, "platform": platform, "offer_type": offer_type,
                            "price": price, "target": target, "budget": test_budget,
                            "niche": niche, "competitors": competitors, "brand_type": brand_type,
                        })
                        st.session_state.profiles = load_profiles()
                        st.success(f"Profil '{new_prof_name}' sauvegardé !")
                    else:
                        st.error("Donnez un nom au profil.")
            # Valeurs par défaut si options avancées pas ouvertes
            if 'model' not in dir():       model       = "gpt-4o-mini"
            if 'price' not in dir():       price       = pval("price","")
            if 'target' not in dir():      target      = pval("target","")
            if 'test_budget' not in dir(): test_budget = pval("budget","")
            if 'niche' not in dir():       niche       = pval("niche","")
            if 'competitors' not in dir(): competitors = pval("competitors","")

            market_context = "\n".join([
                "Prix : "        + (price       or "Non renseigne"),
                "Cible : "       + (target      or "Non renseigne"),
                "Budget : "      + (test_budget or "Non renseigne"),
                "Niche : "       + (niche       or "Non renseigne"),
                "Concurrents : " + (competitors or "Non renseigne"),
            ])

            st.markdown("")
            run_btn = st.button("🚀 Lancer l'audit", type="primary", use_container_width=True)

        with col_r:
            if st.session_state.loaded_result and not run_btn:
                st.caption("Résultat chargé depuis l'historique")
                render_results(st.session_state.loaded_result)
                if st.button("✕ Fermer", key="close_loaded"):
                    st.session_state.loaded_result = None
                    st.rerun()
                st.stop()

            if not run_btn:
                # ── Page d'accueil col droite ─────────────────
                st.markdown(
                    """<div style='background:#0f0f1a;border:1px solid #1e1e3a;border-radius:12px;
                        padding:28px 32px;margin-top:8px'>
                      <div style='color:#6366f1;font-size:0.75rem;font-weight:600;
                           text-transform:uppercase;letter-spacing:1px;margin-bottom:12px'>
                        Comment ça marche
                      </div>
                      <div style='color:#ccc;font-size:0.92rem;line-height:1.9'>
                        <span style='color:#6366f1;font-weight:700'>①</span>&nbsp;
                        Collez l'URL de votre landing page<br>
                        <span style='color:#6366f1;font-weight:700'>②</span>&nbsp;
                        Choisissez votre plateforme et type d'offre<br>
                        <span style='color:#6366f1;font-weight:700'>③</span>&nbsp;
                        Cliquez <strong>Lancer l'audit</strong> — résultats en ~15s
                      </div>
                    </div>""",
                    unsafe_allow_html=True,
                )
                st.markdown("")
                # Modes
                m1, m2, m3 = st.columns(3)
                for col, title, desc, color in [
                    (m1, "Funnel Only", "Score /20 · Analyse · Rewrite", "#6366f1"),
                    (m2, "Ads Only",    "Score /20 · Hooks · Variantes", "#22c55e"),
                    (m3, "Full Risk",   "Audit complet + Message Match", "#FF8C00"),
                ]:
                    with col:
                        st.markdown(
                            f"""<div style='background:#0f0f1a;border:1px solid #1e1e3a;
                                border-top:3px solid {color};border-radius:10px;
                                padding:14px 16px;text-align:center'>
                              <div style='color:#fff;font-weight:700;font-size:0.88rem'>{title}</div>
                              <div style='color:#666;font-size:0.78rem;margin-top:4px'>{desc}</div>
                            </div>""",
                            unsafe_allow_html=True,
                        )
                st.stop()

            errors = []
            if mode in ("Funnel Only", "Full Risk") and not landing_url.strip():
                errors.append("URL landing page requise")
            if mode in ("Ads Only", "Full Risk") and not ad_text.strip():
                errors.append("Texte de la pub requis")
            for err in errors: st.error(err)
            if errors: st.stop()

            detected_page_type = "Non applicable (mode Ads Only)"
            page_lang          = "fr"
            if mode in ("Funnel Only", "Full Risk") and landing_url.strip():
                with st.spinner("Extraction du contenu de la page..."):
                    landing_content, status, is_js_page = extract_page(landing_url.strip())
                st.info(status)
                if not landing_content:
                    st.error("Impossible d'extraire le contenu. Verifiez l'URL.")
                    st.stop()

                # Warning page JavaScript
                if is_js_page:
                    st.warning(
                        "⚠️ **Page JavaScript détectée** — Cette page semble être rendue dynamiquement "
                        "(React, Next.js, Shopify Hydrogen, etc.). LRS n'a peut-être pas lu tout le contenu visible. "
                        "Le score pourrait être **sous-estimé**. Pour un audit plus précis, copie-colle "
                        "manuellement le texte de la page dans le champ ci-dessous."
                    )
                elif len(landing_content) < 500:
                    st.warning(
                        "⚠️ **Contenu extrait très court** (" + str(len(landing_content)) + " caractères). "
                        "La page n'a peut-être pas été lue correctement. Vérifiez l'aperçu ci-dessous."
                    )

                # Détection langue
                page_lang = detect_language(landing_content)

                # Auto-detection du type de page
                detected_page_type = detect_page_type(landing_content, landing_url.strip())
                lang_label = {"fr": "🇫🇷 Français", "en": "🇬🇧 Anglais", "mixte": "🌐 Mixte", "autre": "❓"}.get(page_lang, "")
                st.caption("🔍 **" + detected_page_type + "**  |  " + lang_label)

                # Aperçu du contenu scrapé
                with st.expander("👁️ Aperçu du contenu extrait (debug)", expanded=False):
                    st.caption("Ce texte est exactement ce que LRS analyse. S'il est vide ou incohérent, le score sera moins fiable.")
                    st.text(landing_content[:1500] + ("..." if len(landing_content) > 1500 else ""))

            result = None
            with st.status("🧠 LRS analyse votre page...", expanded=True) as _audit_status:
                _stage_ph  = st.empty()
                _tokens_ph = st.empty()
                try:
                    result = run_audit_stream(
                        mode, platform, offer_type, landing_content,
                        ad_text, market_context, model,
                        brand_type=brand_type,
                        page_type=detected_page_type,
                        page_lang=page_lang,
                        status_stage=_stage_ph,
                        status_tokens=_tokens_ph,
                    )
                    _audit_status.update(label="✅ Analyse complète !", state="complete", expanded=False)
                except Exception as _e:
                    _audit_status.update(label="❌ Erreur d'analyse", state="error", expanded=False)
                    st.error(str(_e))
                    st.stop()

            if result:
                ts   = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                meta = {"mode": mode, "platform": platform, "offer_type": offer_type,
                        "url": landing_url, "timestamp": ts,
                        "brand_type": brand_type, "page_type": detected_page_type,
                        "ad_text": ad_text, "model": model, "market_context": market_context}
                save_history(result, meta)
                st.session_state.loaded_result = None
                if st.session_state.get("reaudit_url"):
                    st.session_state.reaudit_url = ""
                render_results(result)

                # ── Mode Avant/Après ──────────────────────────────
                history = st.session_state.audit_history
                if len(history) >= 2:
                    with st.expander("📊 Comparer avec un audit précédent (Avant/Après)", expanded=False):
                        prev_options = {
                            f"{e['timestamp']} — {str(e.get('url','') or e.get('offer_type',''))[:40]} — {e['score']}/20": i+1
                            for i, e in enumerate(history[1:], 0)
                        }
                        selected = st.selectbox("Choisir l'audit de référence", list(prev_options.keys()), key="avant_apres_sel")
                        if selected:
                            prev_idx = prev_options[selected]
                            prev = history[prev_idx]
                            cur_score = result.get("_c",{}).get("score",0)
                            prev_score = prev.get("score",0)
                            delta = cur_score - prev_score
                            delta_icon  = "▲" if delta > 0 else "▼" if delta < 0 else "="
                            c1,c2,c3 = st.columns(3)
                            with c1: st.metric("Score précédent", f"{prev_score}/20")
                            with c2: st.metric("Score actuel",    f"{cur_score}/20")
                            with c3: st.metric("Delta", f"{delta_icon} {abs(delta)} pts", delta=delta, delta_color="normal")
                            pc = prev.get("result",{}).get("_c",{})
                            cc = result.get("_c",{})
                            rows = []
                            for label, pk, ck in [("Hook","hook","hook"),("Offer","offer","offer"),
                                                   ("Trust","trust","trust"),("Friction","friction","friction")]:
                                pv = pc.get(pk,0); cv = cc.get(ck,0); dv = cv-pv
                                arrow = "▲" if dv>0 else "▼" if dv<0 else "="
                                color = "🟢" if dv>0 else "🔴" if dv<0 else "⚪"
                                rows.append(f"**{label}** : {pv}/5 → {cv}/5  {color} {arrow}{abs(dv)}")
                            for r in rows: st.markdown(r)

                st.markdown("---")
                # ── Exports ───────────────────────────────────────
                meta["version"] = APP_VERSION
                fname_base = "LRS_" + ts.replace("/","-").replace(":","-").replace(" ","_")
                ecol1, ecol2, ecol3, ecol4 = st.columns(4)
                with ecol1:
                    txt = export_txt(result, meta)
                    st.download_button("📥 .txt", data=txt.encode("utf-8"),
                                       file_name=fname_base+".txt", mime="text/plain",
                                       use_container_width=True)
                with ecol2:
                    if PDF_AVAILABLE:
                        try:
                            pdf_bytes = generate_pdf_report(result, meta)
                            st.download_button("📄 PDF", data=pdf_bytes,
                                               file_name=fname_base+".pdf", mime="application/pdf",
                                               type="primary", use_container_width=True)
                        except Exception as pdf_err:
                            st.caption(f"PDF indisponible : {pdf_err}")
                    else:
                        st.caption("PDF non disponible")
                with ecol3:
                    if PDF_AVAILABLE:
                        with st.expander("👔 Rapport Client"):
                            client_name_tab1 = st.text_input("Nom du client",
                                placeholder="Ex: Startup XYZ", key="client_name_tab1")
                            if st.button("Générer", key="gen_client_pdf"):
                                try:
                                    meta_c = {**meta, "client_name": client_name_tab1 or "",
                                              "report_mode": "client"}
                                    pdf_c = generate_pdf_report(result, meta_c)
                                    st.download_button("⬇️ Télécharger", data=pdf_c,
                                        file_name=fname_base+"_client.pdf", mime="application/pdf",
                                        key="dl_client_pdf")
                                except Exception as ce:
                                    st.error(f"Erreur : {ce}")
                with ecol4:
                    render_email_widget(result, meta, key_prefix="tab1_email")

                # Share widget full-width below exports
                render_share_widget(result, meta, key_prefix="tab1_share")

    # ── tab2 : Multi-Audit (Bulk + Comparaison) ──────────────
    with tab2:
        sub1, sub2 = st.tabs(["⚡ Bulk — Plusieurs URLs", "⚔️ Comparaison — 2 pages"])
        with sub1:
            render_bulk(api_key)
        with sub2:
            render_comparison(api_key)

    # ── tab3 : Suivi (Projets + Monitoring) ──────────────────
    with tab3:
        sub3, sub4 = st.tabs(["🗂️ Projets", "📡 Monitoring & Alertes"])
        with sub3:
            render_projects(api_key)
        with sub4:
            render_monitoring(api_key)

    # ── tab4 : Historique ────────────────────────────────────
    with tab4:
        render_history()

    # ── tab5 : Ressources (Checklist + Benchmark + Changelog) ─
    with tab5:
        sub5, sub6, sub7, sub8 = st.tabs([
            "✅ Checklist", "📚 Ads Library", "📊 Benchmark 2025", "📋 Changelog"
        ])
        with sub5:
            render_checklist()
        with sub6:
            render_ads_library()
        with sub7:
            render_benchmark_tab()
        with sub8:
            render_changelog()


if __name__ == "__main__":
    main()

# LRS - Launch Risk System V2.3
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
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

APP_VERSION    = "2.3"
MAX_PAGE_CHARS = 8000

st.set_page_config(
    page_title="LRS - Launch Risk System",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

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

# ── HISTORIQUE PERSISTANT ────────────────────────────────────
HISTORY_FILE = os.path.join(os.path.dirname(__file__), ".lrs_history.json")

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

# ── SESSION STATE ────────────────────────────────────────────
def init_session():
    if "audit_history" not in st.session_state:
        # Charger depuis fichier au démarrage
        st.session_state.audit_history = load_history_file()
    if "loaded_result" not in st.session_state:
        st.session_state.loaded_result = None

def save_history(result, meta):
    entry = {**meta, "score": result.get("_c", {}).get("score", 0),
             "decision": result.get("_c", {}).get("decision", ""), "result": result}
    st.session_state.audit_history.insert(0, entry)
    if len(st.session_state.audit_history) > 50:
        st.session_state.audit_history = st.session_state.audit_history[:50]
    # Persister sur disque
    write_history_file(st.session_state.audit_history)

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

    st.markdown("---")
    st.subheader("Résultat LRS")

    # Infos meta depuis lrs
    lrs_meta = result.get("lrs", {})
    brand_type_display = lrs_meta.get("brand_type", "")
    page_type_display  = lrs_meta.get("page_type", "")

    # ── Bandeau score principal ──────────────────────────────
    score_color = RISK_COLORS.get(risk, "#888")
    bar_filled  = round(score / 20 * 10)
    bar_visual  = "█" * bar_filled + "░" * (10 - bar_filled)
    dec_emoji   = "🔴" if risk == "High" else "🟡" if risk == "Moderate" else "🟢"

    st.markdown(
        f"""<div style='background:linear-gradient(135deg,#1a1a2e,#16213e);
            border-left:6px solid {score_color};border-radius:12px;
            padding:20px 28px;margin-bottom:16px'>
          <div style='display:flex;align-items:center;gap:32px;flex-wrap:wrap'>
            <div>
              <div style='color:#aaa;font-size:0.8em;text-transform:uppercase;letter-spacing:1px'>Score LRS</div>
              <div style='color:{score_color};font-size:3.2em;font-weight:900;line-height:1'>{score}<span style='font-size:0.45em;color:#888'> / 20</span></div>
              <div style='color:#555;font-family:monospace;font-size:1.1em'>{bar_visual}</div>
            </div>
            <div style='flex:1;min-width:200px'>
              <div style='color:{score_color};font-size:1.6em;font-weight:800'>{dec_emoji} {dec}</div>
              <div style='color:#aaa;font-size:0.95em;margin-top:4px'>Risk : <strong style='color:{score_color}'>{risk}</strong></div>
            </div>
          </div>
        </div>""",
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        mc = MATCH_COLORS.get(ms, "#888")
        st.markdown("**Message Match**<br><span style='font-size:1.3em;color:" + mc + ";font-weight:800'>" + ms + "</span>", unsafe_allow_html=True)
    with col2: st.metric("Hook",    str(c.get("hook",    0)) + " / 5")
    with col3: st.metric("Offer",   str(c.get("offer",   0)) + " / 5")
    with col4: st.metric("Trust",   str(c.get("trust",   0)) + " / 5")

    if brand_type_display or page_type_display:
        info_parts = []
        if brand_type_display: info_parts.append("🏷️ **" + brand_type_display + "**")
        if page_type_display:  info_parts.append("🔍 " + page_type_display)
        st.caption("  |  ".join(info_parts))

    st.markdown("---")
    st.subheader("Score Breakdown")
    for label, val in [("Hook", c.get("hook", 0)), ("Offer", c.get("offer", 0)),
                       ("Trust", c.get("trust", 0)), ("Friction / Message Match", c.get("friction", 0))]:
        color = "#FF4444" if val <= 2 else "#FF8C00" if val <= 3 else "#22c55e"
        cl, cr = st.columns([4, 1])
        with cl:
            st.markdown("**" + label + "** &nbsp; <span style='font-family:monospace;color:" + color + "'>`" + bar(val) + "`</span>", unsafe_allow_html=True)
        with cr:
            st.markdown("<span style='color:" + color + ";font-weight:700'>" + str(val) + " / 5</span>", unsafe_allow_html=True)

    if c.get("trust", 0) <= 2:
        st.warning("Note Trust basse : L'outil lit uniquement le texte. Les preuves visuelles (photos d'avis, captures) ne sont pas comptees. Verifiez manuellement.")

    st.markdown("---")
    st.subheader("Analyse Detaillee")
    for key, label, val in [("hook_detail", "Hook", c.get("hook", 0)),
                             ("offer_detail", "Offer", c.get("offer", 0)),
                             ("trust_detail", "Trust", c.get("trust", 0)),
                             ("friction_detail", "Friction", c.get("friction", 0))]:
        detail = why.get(key, "")
        if detail:
            with st.expander(label + " -- " + str(val) + "/5", expanded=(val <= 2)):
                st.markdown(detail)

    top3 = why.get("top_3_reasons", [])
    if top3:
        st.markdown("**Top 3 raisons :**")
        for i, r in enumerate(top3, 1):
            st.markdown(str(i) + ". " + r)

    gaps = why.get("critical_gaps", [])
    if gaps:
        st.markdown("**Critical Gaps :**")
        for g in gaps: st.markdown("- " + g)

    if ms not in ("N/A", None, ""):
        st.markdown("---")
        st.subheader("Message Match Analysis")
        expl = mm.get("score_explication", "")
        if expl: st.info(expl)
        ca, cb = st.columns(2)
        with ca:
            mm_list = mm.get("mismatches", [])
            if mm_list:
                st.markdown("**Mismatches :**")
                for m2 in mm_list: st.markdown("- " + m2)
        with cb:
            fixes = mm.get("fix", [])
            if fixes:
                st.markdown("**Corrections :**")
                for f in fixes: st.markdown("- " + f)

    st.markdown("---")
    st.subheader("Estimation CVR (cold traffic, sous hypotheses)")
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("CVR Actuel", c.get("cvr_cur", "N/A"))
    with c2: st.metric("CVR Post-Fix", c.get("cvr_fix", "N/A"))
    with c3: st.metric("Uplift", c.get("cvr_up", "N/A"))
    st.caption("Benchmarks cold traffic. Non garantis.")

    st.markdown("---")
    st.subheader("Plan d'Action Priorise")

    # TOP PRIORITY ACTION — Bug 3
    top_prio = fp.get("top_priority_action", {})
    if top_prio and top_prio.get("what"):
        st.markdown("#### 🎯 Action Prioritaire #1")
        st.error(
            "**" + top_prio.get("what", "") + "**\n\n"
            "**Comment concrètement :** " + top_prio.get("how_exactly", "") + "\n\n"
            "**Impact attendu :** " + top_prio.get("expected_impact", "") + "  |  "
            "**Temps estimé :** " + top_prio.get("time_estimate", "")
        )

    # QUICK WINS — Bug 3
    quick_wins = fp.get("quick_wins", [])
    if quick_wins:
        st.markdown("#### ⚡ Quick Wins (moins d'1h)")
        for qw in quick_wins:
            with st.expander("⚡ " + qw.get("what", "")):
                st.markdown("**Comment concrètement :** " + qw.get("how_exactly", ""))
                st.markdown("**Impact attendu :** " + qw.get("expected_impact", ""))
                st.markdown("**Temps estimé :** `" + qw.get("time_estimate", "<1h") + "`")

    # LONG TERM — Bug 3
    long_term = fp.get("long_term", [])
    if long_term:
        st.markdown("#### 🏗️ Améliorations Long Terme")
        for lt in long_term:
            with st.expander("🏗️ " + lt.get("what", "")):
                st.markdown("**Comment concrètement :** " + lt.get("how_exactly", ""))
                st.markdown("**Impact attendu :** " + lt.get("expected_impact", ""))
                st.markdown("**Temps estimé :** `" + lt.get("time_estimate", "") + "`")

    # PRIORITY ACTIONS (fallback + A/B tests)
    priority_actions = fp.get("priority_actions", [])
    if priority_actions:
        st.markdown("#### 📋 Toutes les Actions")
        for a in priority_actions:
            imp   = a.get("impact", "medium")
            icon2 = "🔴" if imp == "high" else "🟡" if imp == "medium" else "🟢"
            cat   = a.get("category", "")
            cat_label = " ⚡" if cat == "quick_win" else " 🏗️" if cat == "long_term" else ""
            with st.expander(icon2 + cat_label + " " + a.get("what", "") + " [" + imp.upper() + " | " + a.get("effort", "").upper() + "]"):
                how_exactly = a.get("how_exactly", a.get("how", ""))
                st.markdown("**Comment concrètement :** " + how_exactly)
                if a.get("how") and a.get("how_exactly") and a["how"] != a["how_exactly"]:
                    st.markdown("**Résumé :** " + a.get("how", ""))
                st.markdown("**Pourquoi :** " + a.get("why", ""))
                if a.get("time_estimate"):
                    st.markdown("**Temps estimé :** `" + a["time_estimate"] + "`")

    for t in fp.get("ab_tests", []):
        with st.expander("🧪 Test A/B : " + t.get("hypothesis", "")):
            ta, tb = st.columns(2)
            with ta: st.markdown("**A :** " + t.get("variant_a", ""))
            with tb: st.markdown("**B :** " + t.get("variant_b", ""))
            st.markdown("**Métrique :** " + t.get("success_metric", ""))

    st.markdown("---")
    st.subheader("Rewrite Recommandations")
    with st.expander("Voir le rewrite complet", expanded=False):
        if rw.get("headline"):    st.markdown("**Headline :**"); st.info(rw["headline"])
        if rw.get("subheadline"): st.markdown("**Subheadline :**"); st.info(rw["subheadline"])
        bullets = rw.get("hero_bullets", [])
        if bullets:
            st.markdown("**Bullets :**")
            for b in bullets: st.markdown("- " + b)
        if rw.get("cta_primary"):  st.markdown("**CTA :** `" + rw["cta_primary"] + "`")
        if rw.get("proof_block"):  st.markdown("**Proof Block :**"); st.info(rw["proof_block"])
        stack = rw.get("offer_stack", [])
        if stack:
            st.markdown("**Offer Stack :**")
            for o in stack: st.markdown("- " + o)
        if rw.get("guarantee"): st.markdown("**Garantie :** " + rw["guarantee"])
        faqs = rw.get("faq_objections", [])
        if faqs:
            st.markdown("**FAQ :**")
            for q in faqs: st.markdown("- " + q)

    st.markdown("---")
    st.subheader("Ad Creative Recommendations")
    with st.expander("Voir les angles, hooks et variantes", expanded=False):
        angles = ads.get("angles", [])
        if angles:
            st.markdown("**Angles :**")
            for a2 in angles:
                if isinstance(a2, dict):
                    st.markdown("- **" + a2.get("angle", "") + "** -- " + a2.get("rationale", ""))
                else:
                    st.markdown("- " + str(a2))

        hooks = ads.get("hooks", [])
        if hooks:
            st.markdown("**Hooks :**")
            for h in hooks:
                if isinstance(h, dict):
                    st.markdown("- `[" + h.get("platform", "") + "/" + h.get("type", "") + "]` " + h.get("hook", ""))
                else:
                    st.markdown("- " + str(h))

        variants = ads.get("variants", [])
        for i, v in enumerate(variants, 1):
            with st.expander("Variante " + str(i) + " -- " + v.get("platform", "")):
                st.markdown("**Headline :** " + v.get("headline", ""))
                st.text_area("Primary Text", value=v.get("primary_text", ""), height=130, disabled=True, key="pt_" + str(i))
                st.markdown("**CTA :** `" + v.get("cta", "") + "`")

        if ads.get("script_ugc_20s"):
            st.markdown("**Script UGC 20-30s :**")
            st.text_area("Script UGC", value=ads["script_ugc_20s"], height=180, disabled=True)

    st.markdown("---")
    with st.expander("JSON Brut (Debug)", expanded=False):
        st.json(result)

# ── HISTORIQUE ───────────────────────────────────────────────
def render_history():
    st.subheader("Historique des Audits")
    if not st.session_state.audit_history:
        st.info("Aucun audit effectue dans cette session.")
        return

    # ── Graphique d'évolution des scores ─────────────────────
    if len(st.session_state.audit_history) >= 2:
        st.markdown("#### 📈 Évolution des scores")
        history_reversed = list(reversed(st.session_state.audit_history))
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
        st.caption("Seuil vert (15+) = Ready to scale | Seuil orange (10+) = Test small budget | Rouge (<10) = Do NOT launch")
        st.markdown("---")

    for i, entry in enumerate(st.session_state.audit_history):
        score = entry.get("score", 0)
        dec   = entry.get("decision", "")
        label = str(entry.get("url", "") or entry.get("offer_type", ""))[:40]
        color = "#FF4444" if score <= 9 else "#FF8C00" if score <= 14 else "#22c55e"

        with st.expander(entry["timestamp"] + " -- " + entry["mode"] + " -- " + str(score) + "/20 -- " + label):
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("Score", str(score) + "/20")
            with c2: st.markdown("**Decision**<br><span style='color:" + color + "'>" + dec + "</span>", unsafe_allow_html=True)
            with c3: st.markdown("**Plateforme**<br>" + entry.get("platform", ""), unsafe_allow_html=True)

            if st.button("Recharger", key="reload_" + str(i)):
                st.session_state.loaded_result = entry["result"]
                st.rerun()

            txt   = export_txt(entry["result"], entry)
            fname = "LRS_" + entry["timestamp"].replace("/", "-").replace(":", "-").replace(" ", "_") + ".txt"
            st.download_button("Exporter .txt", data=txt.encode("utf-8"),
                               file_name=fname, mime="text/plain", key="exp_" + str(i))

# ── MAIN ─────────────────────────────────────────────────────
# ── CONTROLE D'ACCES PAR MOT DE PASSE ───────────────────────
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

    if not check_access():
        st.stop()

    st.markdown("# 🚦 LRS - Launch Risk System")
    st.markdown("**V" + APP_VERSION + "** — Paid Traffic Pre-Launch Audit — Strict Scoring")

    # Verification cle API
    api_key = get_api_key()
    if not api_key:
        st.error(
            "**Cle API OpenAI manquante.** Ajoutez `OPENAI_API_KEY=sk-...` dans votre fichier `.env` "
            "(local) ou dans Streamlit Cloud > App settings > Secrets."
        )
        with st.expander("Comment configurer la cle API ?"):
            st.markdown("""
**En local :**
1. Copiez `.env.example` en `.env`
2. Remplacez `sk-your-openai-api-key-here` par votre vraie cle

**Sur Streamlit Cloud :**
1. Allez dans votre app > `⋮` > `Settings` > `Secrets`
2. Ajoutez :
```toml
OPENAI_API_KEY = "sk-..."
```
            """)
        st.stop()

    tab1, tab2, tab3 = st.tabs(["Audit", "Checklist Pre-Lancement", "Historique"])

    with tab1:
        col_l, col_r = st.columns([1, 2])

        with col_l:
            st.subheader("Configuration")
            mode       = st.selectbox("Mode d'audit", ["Funnel Only", "Ads Only", "Full Risk"])
            platform   = st.selectbox("Plateforme", ["Meta", "TikTok", "Google", "Mixed", "N/A"])
            offer_type = st.selectbox("Type d'offre", ["Digital product", "Ecom (produit physique)"])
            model      = st.selectbox(
                "Modele OpenAI",
                ["gpt-4o-mini", "gpt-4o"],
                help="gpt-4o-mini : rapide et economique (~0.01$/audit). gpt-4o : plus precis (~0.10$/audit)."
            )

            st.markdown("---")
            st.markdown("**Contexte Marche** (ameliore la precision)")
            price       = st.text_input("Prix du produit",  placeholder="Ex: 47 euros")
            target      = st.text_input("Cible / Persona",  placeholder="Ex: adultes 25-45 ans, insomnies")
            test_budget = st.text_input("Budget test",      placeholder="Ex: 300 euros/semaine")
            niche       = st.text_input("Niche / Marche",   placeholder="Ex: wellness, mindset")
            competitors = st.text_input("Concurrents",      placeholder="Ex: Calm, Headspace")

            market_context = "\n".join([
                "Prix : "        + (price       or "Non renseigne"),
                "Cible : "       + (target      or "Non renseigne"),
                "Budget : "      + (test_budget or "Non renseigne"),
                "Niche : "       + (niche       or "Non renseigne"),
                "Concurrents : " + (competitors or "Non renseigne"),
            ])

            st.markdown("---")
            brand_type = st.radio(
                "Type de marque",
                ["Nouveau lancement", "Marque etablie"],
                help="**Marque etablie** = marque avec notoriete existante (ex: Gymshark, Nike, Sephora). "
                     "Le scoring Trust sera adapte pour tenir compte de la reputation de marque.\n\n"
                     "**Nouveau lancement** = scoring strict 100% base sur les elements de la page.",
                horizontal=True,
            )

            st.markdown("---")
            landing_url     = ""
            landing_content = ""
            if mode in ("Funnel Only", "Full Risk"):
                landing_url = st.text_input("URL Landing Page", placeholder="https://exemple.com/page")

            ad_text = ""
            if mode in ("Ads Only", "Full Risk"):
                ad_text = st.text_area("Texte / Script pub", placeholder="Primary text, headline, script...", height=150)

            st.markdown("---")
            run_btn = st.button("🚀 Run LRS Audit", type="primary", use_container_width=True)

        with col_r:
            if st.session_state.loaded_result and not run_btn:
                st.info("Resultat charge depuis l'historique")
                render_results(st.session_state.loaded_result)
                if st.button("Effacer"):
                    st.session_state.loaded_result = None
                    st.rerun()
                st.stop()

            if not run_btn:
                st.markdown("### Configurez votre audit a gauche puis cliquez Run LRS Audit")
                st.markdown("""
| Mode | Ce que vous obtenez |
|------|---------------------|
| **Funnel Only** | Score /20, analyse detaillee, rewrite complet |
| **Ads Only** | Score /20, hooks, angles, variantes prets |
| **Full Risk** | Audit complet + Message Match + Plan d'action |

Remplissez le contexte marche pour des recommandations personnalisees.
                """)
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

            with st.spinner("Analyse LRS en cours... (10-30 secondes)"):
                try:
                    result = run_audit(mode, platform, offer_type, landing_content,
                                       ad_text, market_context, model,
                                       brand_type=brand_type,
                                       page_type=detected_page_type,
                                       page_lang=page_lang)
                    ts   = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                    meta = {"mode": mode, "platform": platform, "offer_type": offer_type,
                            "url": landing_url, "timestamp": ts,
                            "brand_type": brand_type, "page_type": detected_page_type}
                    save_history(result, meta)
                    st.session_state.loaded_result = None
                    render_results(result)
                    st.markdown("---")
                    txt   = export_txt(result, meta)
                    fname = "LRS_" + ts.replace("/", "-").replace(":", "-").replace(" ", "_") + ".txt"
                    st.download_button("📥 Exporter le rapport (.txt)", data=txt.encode("utf-8"),
                                       file_name=fname, mime="text/plain")
                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error("Erreur inattendue : " + str(e))

    with tab2:
        render_checklist()

    with tab3:
        render_history()


if __name__ == "__main__":
    main()

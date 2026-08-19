# LRS — Audit Engine (module autonome, sans dépendance Streamlit)
#
# Extrait de app.py pour le pilote UI Apple-style (FastAPI + frontend custom).
# Contient uniquement : extraction de page, détection de langue/type de page,
# et l'appel OpenAI qui produit le score LRS. Utilisé par pilot_server.py.
#
# Ce module duplique volontairement (pour l'instant) une partie de la logique
# encore présente dans app.py, le temps de valider le pilote. Si la migration
# est confirmée, app.py importera directement d'ici au lieu de dupliquer.

import json
import os
import re
import time
from html.parser import HTMLParser

import requests
import trafilatura

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAX_PAGE_CHARS = 8000

# Modele Claude par defaut pour l'audit — aligne sur
# creative_studio/core/llm_client.py::DEFAULT_MODEL.
DEFAULT_ANTHROPIC_MODEL = "claude-opus-5"


def load_txt(filename):
    try:
        with open(os.path.join(_BASE_DIR, filename), "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def clamp(text, n=MAX_PAGE_CHARS):
    return text[:n] + "[TRONQUE]" if len(text) > n else text


def get_api_key():
    key = os.getenv("OPENAI_API_KEY", "")
    if key and key.startswith("sk-"):
        return key
    return ""


def get_anthropic_api_key():
    """Miroir de get_api_key() pour Claude — meme pattern que
    creative_studio/core/llm_client.py::get_anthropic_api_key()."""
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if key and key.startswith("sk-ant-"):
        return key
    return ""


# ── DÉTECTION LANGUE ───────────────────────────────────────────
def detect_language(text: str) -> str:
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
    if len(extracted) < 400 and len(html) > 5000:
        return True
    js_signals = ["__next", "__nuxt", "react-root", "ng-version", "data-reactroot",
                  "window.__INITIAL_STATE__", "window.__PRELOADED_STATE__", "_app.js",
                  "chunk.js", "bundle.js"]
    html_low = html[:10000].lower()
    return sum(1 for s in js_signals if s in html_low) >= 2


# ── EXTRACTION PAGE WEB ─────────────────────────────────────────
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
        full = extracted.strip()
        above_fold = full[:2000]
        rest = full[2000:]
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
            if tag in self.skip_tags:
                self.skip = True

        def handle_endtag(self, tag):
            if tag in self.skip_tags:
                self.skip = False

        def handle_data(self, data):
            t = data.strip()
            if not self.skip and len(t) > 20:
                self.parts.append(t)

    try:
        p = HP()
        p.feed(html)
        fb = "\n".join(p.parts)
        if len(fb) > 100:
            return clamp(fb), f"Extraction partielle ({len(fb[:MAX_PAGE_CHARS])} caracteres)", is_js
    except Exception:
        pass

    return html[:2000], "Extraction faible.", True


# ── DÉTECTION TYPE DE PAGE ──────────────────────────────────────
def detect_page_type(content: str, url: str = "") -> str:
    if not content:
        return "Type inconnu (page vide)"

    text = content.lower()
    url_l = url.lower()

    product_page_patterns = [
        r"/products?/[^/]+/?$", r"/p/[^/]+/?$", r"/item/[^/]+/?$",
        r"/shop/[^/]+/[^/]+/?$", r"/articles?/[^/]+/?$", r"[?&](product|sku|pid|ref)=",
    ]
    for pattern in product_page_patterns:
        if re.search(pattern, url_l):
            product_confirm = ["ajouter au panier", "add to cart", "acheter", "buy",
                               "taille", "couleur", "size", "color", "quantite", "qty",
                               "en stock", "in stock", "livraison", "shipping", "avis", "reviews"]
            if sum(1 for s in product_confirm if s in text) >= 2:
                return "Page Produit Ecom (fiche produit individuelle) (confiance : haute)"

    catalogue_url_patterns = [r"/collections?/", r"/categor", r"/boutique/?$",
                               r"/shop/?$", r"/store/?$", r"/magasin"]
    for pattern in catalogue_url_patterns:
        if re.search(pattern, url_l):
            return "Page Catalogue Ecom (plusieurs produits) (confiance : haute)"

    blog_url_patterns = [r"/blog/", r"/articles?/", r"/posts?/", r"/actualite",
                         r"/news/", r"/magazine/"]
    for pattern in blog_url_patterns:
        if re.search(pattern, url_l):
            return "Blog / Article (confiance : haute)"

    url_path = re.sub(r"https?://[^/]+", "", url_l).rstrip("/")
    if url_path in ("", "/", "/fr", "/en", "/fr/", "/en/"):
        return "Page d'accueil / Homepage (confiance : haute)"

    scores = {
        "Page Produit Ecom (fiche produit individuelle)": 0,
        "Sales Page / Landing Page (offre unique)": 0,
        "Page Catalogue Ecom (plusieurs produits)": 0,
        "Page SaaS / Logiciel": 0,
        "Page d'accueil / Homepage": 0,
        "Blog / Article": 0,
        "Page Lead Gen (capture email)": 0,
    }

    product_signals = ["ajouter au panier", "add to cart", "taille", "couleur", "size",
                       "color", "quantite", "qty", "en stock", "rupture de stock",
                       "livraison sous", "retours gratuits", "materiau", "composition",
                       "guide des tailles", "size guide", "avis verifies", "note globale",
                       "recommandent ce produit", "achetez avec"]
    scores["Page Produit Ecom (fiche produit individuelle)"] += sum(2 for s in product_signals if s in text)

    sales_signals = ["commander maintenant", "achetez maintenant", "buy now", "offre limitee",
                     "bonus", "valeur totale", "ce que vous obtenez", "what you get",
                     "place limitee", "testimonial", "100% satisfait", "garantie remboursement",
                     "sans risque", "prix special", "formation", "programme", "module",
                     "resultats", "transformation", "methode", "systeme"]
    scores["Sales Page / Landing Page (offre unique)"] += sum(2 for s in sales_signals if s in text)

    catalogue_signals = ["filtrer", "trier par", "filter by", "sort by", "nos produits",
                         "shop all", "toute la collection", "voir tous", "categories",
                         "nouveautes", "meilleures ventes", "best sellers", "promotions"]
    scores["Page Catalogue Ecom (plusieurs produits)"] += sum(2 for s in catalogue_signals if s in text)

    saas_signals = ["essai gratuit", "free trial", "pricing", "tarifs", "plans",
                    "fonctionnalites", "features", "integrations", "api", "dashboard",
                    "abonnement", "per month", "par mois", "demo", "book a demo",
                    "logiciel", "software", "automatiser", "automatisation"]
    scores["Page SaaS / Logiciel"] += sum(2 for s in saas_signals if s in text)

    home_signals = ["notre mission", "qui sommes-nous", "about us", "decouvrez nos",
                    "notre histoire", "we are", "bienvenue", "nos valeurs", "notre equipe"]
    scores["Page d'accueil / Homepage"] += sum(1 for s in home_signals if s in text)

    blog_signals = ["min de lecture", "minute read", "publie le", "par l'auteur",
                    "commentaires", "partager cet article", "share this", "lire la suite",
                    "read more", "tags:", "categorie:", "auteur:"]
    scores["Blog / Article"] += sum(2 for s in blog_signals if s in text)

    leadgen_signals = ["entrez votre email", "enter your email", "inscrivez-vous gratuitement",
                       "telechargez", "download", "guide gratuit", "free guide", "webinar",
                       "masterclass", "challenge", "liste d'attente", "waitlist",
                       "acces immediat", "immediate access"]
    scores["Page Lead Gen (capture email)"] += sum(2 for s in leadgen_signals if s in text)

    best_type = max(scores, key=lambda k: scores[k])
    best_score = scores[best_type]

    if best_score < 2:
        return "Type non determine — scoring applique comme Sales Page standard"

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    second_score = sorted_scores[1][1] if len(sorted_scores) > 1 else 0
    confidence = "haute" if best_score >= 6 and best_score > second_score * 1.5 else "moderee"

    return f"{best_type} (confiance : {confidence})"


# ── BENCHMARKS CVR ──────────────────────────────────────────────
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


# ── PROMPT SYSTÈME ──────────────────────────────────────────────
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
    "IMPORTANT : Cite des elements REELS et PRECIS du contenu analyse. Ne jamais laisser de valeurs generiques.\n"
    "\n"
    "Pour chaque action dans fix_plan, tu DOIS fournir :\n"
    "- 'how_exactly' : les instructions concretes etape par etape\n"
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


def build_methodology_context(mode, offer_type):
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


def _brand_context(brand_type):
    if brand_type == "Marque etablie":
        return (
            "TYPE : Marque etablie (notoriete existante).\n"
            "INSTRUCTION SCORING TRUST : prend en compte la reputation de marque. "
            "Ne pas penaliser trust uniquement sur absence de reviews si marque connue.\n"
            "INSTRUCTION HOOK/OFFER : marques etablies peuvent avoir hooks moins agressifs."
        )
    return (
        "TYPE : Nouveau lancement (cold traffic pur).\n"
        "INSTRUCTION SCORING TRUST : Scoring strict — prouver valeur uniquement via elements visibles.\n"
        "INSTRUCTION HOOK/OFFER : Sois exigeant — doit compenser absence de notoriete."
    )


def _page_type_instructions(page_type):
    pt = page_type.lower()
    if "produit ecom" in pt or "fiche produit" in pt:
        return ("ADAPTATION SCORING PAGE PRODUIT ECOM : note 3/5 si titre clair, "
                "ne pas sur-penaliser navigation. Propose améliorations réalistes pour page produit.")
    if "catalogue" in pt:
        return ("ADAPTATION SCORING CATALOGUE : HOOK 1-2/5 normal, FRICTION moderee normale. "
                "Recommande landing page dédiée pour paid traffic.")
    if "homepage" in pt or "accueil" in pt:
        return ("ADAPTATION SCORING HOMEPAGE : scores bas Hook/Friction normaux. "
                "INSISTE sur nécessité landing page dédiée pour paid traffic.")
    if "saas" in pt or "logiciel" in pt:
        return ("ADAPTATION SCORING SAAS : HOOK = clarté proposition valeur, "
                "OFFER = pricing/free trial, TRUST = logos/témoignages, FRICTION = form simple.")
    if "lead gen" in pt:
        return ("ADAPTATION SCORING LEAD GEN : OFFER = valeur perçue lead magnet, "
                "FRICTION = formulaire simple (1 champ = 5/5).")
    if "blog" in pt or "article" in pt:
        return ("ADAPTATION SCORING BLOG : interprete scores dans contexte éditorial. "
                "Propose amélioration CTAs article.")
    return "Applique le scoring standard landing page de conversion paid traffic."


def _lang_instruction(page_lang):
    if page_lang == "en":
        return "LANGUE : Anglais. Cite éléments en anglais, réponses JSON en français."
    if page_lang == "mixte":
        return "LANGUE : Mixte FR+EN. Cite dans langue originale, JSON en français."
    return "LANGUE DE LA PAGE : Français."


class _AuditJSONParseError(Exception):
    """Levee par _parse_audit_json(strict=True) quand le JSON du LLM est
    illisible. Sert de signal interne pour retenter l'appel (voir
    _run_audit_openai/_run_audit_claude) au lieu de retourner silencieusement
    un score 0/20 fictif des la premiere reponse malformee — c'est ce qui
    causait de faux "0/20" perçus comme un vrai verdict par l'utilisateur."""


def _parse_audit_json(raw_text, mode, platform, offer_type, strict=False):
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
        if strict:
            raise _AuditJSONParseError("JSON illisible")
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


# ── CONSTRUCTION DU PROMPT (partagee entre les deux moteurs) ────
def _build_audit_prompt(mode, platform, offer_type, landing_content, ad_text, market_context,
                         brand_type, page_type, page_lang):
    """Construit (system, user_prompt) — identique quel que soit le LLM appele
    ensuite, pour que le score/comportement ne depende pas du moteur."""
    methodology_context = build_methodology_context(mode, offer_type)

    system = (
        SYSTEM_PROMPT_BASE
        .replace("BRAND_CONTEXT_PLACEHOLDER", _brand_context(brand_type))
        .replace("MARKET_CONTEXT_PLACEHOLDER", market_context)
        .replace("PAGE_TYPE_PLACEHOLDER", page_type + "\n\n" + _page_type_instructions(page_type) + "\n\n" + _lang_instruction(page_lang))
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
    return system, "\n".join(user_parts)


# ── APPEL OPENAI (version synchrone, pour l'API) ────────────────
def _run_audit_openai(mode, platform, offer_type, landing_content, ad_text, market_context, model,
                       brand_type="Nouveau lancement", page_type="Non determine", page_lang="fr"):
    if OpenAI is None:
        raise ValueError("Librairie openai non installee. Relancez : pip install openai")

    api_key = get_api_key()
    if not api_key:
        raise ValueError("Cle API OpenAI manquante. Ajoutez OPENAI_API_KEY dans votre fichier .env.")

    client = OpenAI(api_key=api_key)
    system, user_prompt = _build_audit_prompt(mode, platform, offer_type, landing_content, ad_text,
                                               market_context, brand_type, page_type, page_lang)

    raw = ""
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.15,
                max_tokens=4500,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content or ""
            return _parse_audit_json(raw, mode, platform, offer_type, strict=True)
        except _AuditJSONParseError:
            # JSON illisible malgre response_format=json_object : on retente
            # comme une erreur reseau plutot que de retourner un score 0/20
            # fictif des la premiere reponse malformee.
            if attempt < 2:
                time.sleep(2 ** attempt)
                continue
            break
        except Exception as e:
            last_err = str(e)
            if "api_key" in last_err.lower() or "authentication" in last_err.lower():
                raise ValueError("Cle API invalide ou expiree. Verifiez votre OPENAI_API_KEY.")
            if "quota" in last_err.lower() or "billing" in last_err.lower():
                raise ValueError("Quota OpenAI epuise. Verifiez votre solde sur platform.openai.com.")
            if attempt < 2:
                time.sleep(2 ** attempt)
                continue
            if "rate_limit" in last_err.lower():
                raise ValueError("Rate limit OpenAI atteint apres 3 tentatives. Attendez et relancez.")
            raise ValueError("Erreur OpenAI apres 3 tentatives : " + last_err)

    # 3 tentatives, JSON toujours illisible : on retombe sur le resultat
    # "Analyse incomplete" (comportement historique) plutot que de planter
    # l'appelant — mais l'utilisateur a maintenant eu 3 vraies chances
    # d'obtenir un score reel avant d'en arriver la.
    return _parse_audit_json(raw, mode, platform, offer_type, strict=False)


# ── APPEL CLAUDE (squelette — meme contrat que _run_audit_openai) ──
def _run_audit_claude(mode, platform, offer_type, landing_content, ad_text, market_context,
                       model=DEFAULT_ANTHROPIC_MODEL,
                       brand_type="Nouveau lancement", page_type="Non determine", page_lang="fr"):
    if anthropic is None:
        raise ValueError("Librairie anthropic non installee. Relancez : pip install anthropic")

    api_key = get_anthropic_api_key()
    if not api_key:
        raise ValueError("Cle API Claude manquante. Ajoutez ANTHROPIC_API_KEY dans votre fichier .env.")

    client = anthropic.Anthropic(api_key=api_key)
    system, user_prompt = _build_audit_prompt(mode, platform, offer_type, landing_content, ad_text,
                                               market_context, brand_type, page_type, page_lang)

    raw = ""
    for attempt in range(3):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=4500,
                temperature=0.15,
                system=system,
                messages=[{"role": "user", "content": user_prompt}],
            )
            text_block = next((b for b in response.content if getattr(b, "type", None) == "text"), None)
            raw = text_block.text if text_block is not None else ""
            return _parse_audit_json(raw, mode, platform, offer_type, strict=True)
        except _AuditJSONParseError:
            # Meme logique que _run_audit_openai : JSON illisible -> on
            # retente plutot que de fabriquer un score 0/20 des le 1er coup.
            if attempt < 2:
                time.sleep(2 ** attempt)
                continue
            break
        except Exception as e:
            last_err = str(e)
            low = last_err.lower()
            if "authentication" in low or "api_key" in low or "x-api-key" in low:
                raise ValueError("Cle API Claude invalide ou expiree. Verifiez votre ANTHROPIC_API_KEY.")
            if "credit balance" in low or "billing" in low:
                raise ValueError("Credit Claude epuise. Verifiez votre solde sur console.anthropic.com.")
            if attempt < 2:
                time.sleep(2 ** attempt)
                continue
            if "rate_limit" in low or "overloaded" in low:
                raise ValueError("Rate limit Claude atteint apres 3 tentatives. Attendez et relancez.")
            raise ValueError("Erreur Claude apres 3 tentatives : " + last_err)

    return _parse_audit_json(raw, mode, platform, offer_type, strict=False)


# ── POINT D'ENTREE UNIQUE — bascule de moteur ────────────────────
def run_audit(mode, platform, offer_type, landing_content, ad_text, market_context, model,
              brand_type="Nouveau lancement", page_type="Non determine", page_lang="fr"):
    """Point d'entree unique de l'audit, appele par pilot_server.py.

    Prefere Claude des que ANTHROPIC_API_KEY est configuree (moteur cible de
    la migration). Sans cette cle, retombe automatiquement sur OpenAI —
    comportement strictement inchange tant que la cle Claude n'est pas
    ajoutee, pour ne pas casser l'audit en production le temps de la
    migration. `model` reste le nom de modele OpenAI utilise dans la
    branche de secours ; la branche Claude utilise DEFAULT_ANTHROPIC_MODEL.
    """
    if get_anthropic_api_key():
        return _run_audit_claude(mode, platform, offer_type, landing_content, ad_text, market_context,
                                  brand_type=brand_type, page_type=page_type, page_lang=page_lang)
    return _run_audit_openai(mode, platform, offer_type, landing_content, ad_text, market_context, model,
                              brand_type=brand_type, page_type=page_type, page_lang=page_lang)


# ── GÉNÉRATION D'ANGLES CRÉATIFS (à partir d'une offre, sans landing page) ──
def generate_creative_angles(offer_description, platform, offer_type, model="gpt-4o-mini"):
    if OpenAI is None:
        raise ValueError("Librairie openai non installee. Relancez : pip install openai")

    api_key = get_api_key()
    if not api_key:
        raise ValueError("Cle API OpenAI manquante. Ajoutez OPENAI_API_KEY dans votre fichier .env.")

    client = OpenAI(api_key=api_key)
    system = (
        "Tu es un copywriter senior specialise en paid traffic (Meta/TikTok/Google Ads). "
        "Tu generes des angles publicitaires, hooks et un script UGC a partir d'une offre. "
        "Reponds UNIQUEMENT en JSON, en francais, sans texte hors du JSON."
    )
    user_prompt = (
        "OFFRE : " + offer_description + "\n"
        "PLATEFORME : " + platform + " | TYPE D'OFFRE : " + offer_type + "\n\n"
        "Genere :\n"
        "- 3 angles publicitaires distincts (angle + rationale)\n"
        "- 5 hooks varies (question, statistique, douleur, controverse, curiosite)\n"
        "- 3 variantes de publicite complete (primary_text, headline, cta)\n"
        "- 1 script UGC de 20 secondes\n\n"
        "Format JSON exact :\n"
        '{"angles":[{"angle":"X","rationale":"X"}],'
        '"hooks":[{"hook":"X","type":"question"}],'
        '"variants":[{"primary_text":"X","headline":"X","cta":"X"}],'
        '"script_ugc_20s":"X"}'
    )

    response = None
    last_err = None
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"},
            )
            break
        except Exception as e:
            last_err = str(e)
            if "api_key" in last_err.lower() or "authentication" in last_err.lower():
                raise ValueError("Cle API invalide ou expiree. Verifiez votre OPENAI_API_KEY.")
            if "quota" in last_err.lower() or "billing" in last_err.lower():
                raise ValueError("Quota OpenAI epuise. Verifiez votre solde sur platform.openai.com.")
            if attempt < 2:
                time.sleep(2 ** attempt)
            else:
                raise ValueError("Erreur OpenAI apres 3 tentatives : " + last_err)

    if response is None:
        raise ValueError("Erreur OpenAI : pas de reponse apres 3 tentatives.")

    raw = response.choices[0].message.content or ""
    try:
        data = json.loads(raw)
    except Exception:
        data = {}
    return {
        "angles": data.get("angles", []) if isinstance(data, dict) else [],
        "hooks": data.get("hooks", []) if isinstance(data, dict) else [],
        "variants": data.get("variants", []) if isinstance(data, dict) else [],
        "script_ugc_20s": data.get("script_ugc_20s", "") if isinstance(data, dict) else "",
    }

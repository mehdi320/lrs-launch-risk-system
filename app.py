# LRS - Launch Risk System V2.1
# Paid Traffic Pre-Launch Audit Tool
# Built with Streamlit + OpenAI

import streamlit as st
import requests
import trafilatura
import json
import os
import datetime
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

APP_VERSION    = "2.1"
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

# ── SESSION STATE ────────────────────────────────────────────
def init_session():
    if "audit_history" not in st.session_state:
        st.session_state.audit_history = []
    if "loaded_result" not in st.session_state:
        st.session_state.loaded_result = None

def save_history(result, meta):
    entry = {**meta, "score": result.get("_c", {}).get("score", 0),
             "decision": result.get("_c", {}).get("decision", ""), "result": result}
    st.session_state.audit_history.insert(0, entry)
    if len(st.session_state.audit_history) > 20:
        st.session_state.audit_history = st.session_state.audit_history[:20]

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

def extract_page(url):
    headers = {"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        html = r.text
    except requests.exceptions.ConnectionError:
        return "", "Impossible de se connecter."
    except requests.exceptions.Timeout:
        return "", "Timeout."
    except Exception as e:
        return "", str(e)

    extracted = trafilatura.extract(html, include_links=False, include_images=False, no_fallback=False)
    if extracted and len(extracted.strip()) > 200:
        return clamp(extracted.strip()), f"Contenu extrait ({len(extracted[:MAX_PAGE_CHARS])} caracteres)"

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
            return clamp(fb), f"Extraction partielle ({len(fb[:MAX_PAGE_CHARS])} caracteres)"
    except Exception:
        pass

    return html[:2000], "Extraction faible."

# ── PROMPT SYSTEME ───────────────────────────────────────────
SYSTEM_PROMPT_BASE = (
    "Tu es LRS - Launch Risk System V2, un auditeur paid traffic senior.\n"
    "LANGUE : Reponds TOUJOURS en francais. Tous les textes du JSON en francais.\n"
    "\n"
    "CONTEXTE MARCHE :\n"
    "MARKET_CONTEXT_PLACEHOLDER\n"
    "\n"
    "METHODOLOGIE DE REFERENCE :\n"
    "METHODOLOGY_PLACEHOLDER\n"
    "\n"
    "SCORING STRICT - note uniquement ce qui est PRESENT :\n"
    "HOOK /5 : 5=hook visceral+specifique+tension | 4=hook clair sans tension | 3=generique | 2=confus | 1=pas de hook | 0=aucun\n"
    "OFFER /5 : 5=stack+prix ancre+garantie near CTA+urgence | 4=offre claire sans stack | 3=offre basique | 2=confuse | 1=incomprehensible | 0=aucune\n"
    "TRUST /5 : 5=50+ reviews+photos+garantie near CTA | 4=reviews sans photos | 3=reviews generiques | 2=peu de proof | 1=aucune review | 0=rien\n"
    "FRICTION /5 : 5=zero friction+CTA repete+message coherent | 4=legere friction | 3=friction moderee | 2=friction forte | 1=mismatch evident | 0=impossible\n"
    "\n"
    "DECISION : 0-9=Do NOT launch+High | 10-14=Test small budget+Moderate | 15-20=Ready to scale+Low\n"
    "\n"
    "IMPORTANT : Cite des elements REELS et PRECIS du contenu analyse. Ne jamais laisser de valeurs generiques.\n"
    "\n"
    "Retourne UNIQUEMENT ce JSON valide, rien d'autre :\n"
    "{\n"
    '  "lrs": {"mode":"X","platform":"X","offer_type":"X","score_breakdown_5":{"hook":0,"offer":0,"trust":0,"friction_message_match":0}},\n'
    '  "message_match": {"status":"N/A","score_explication":"X","mismatches":[],"fix":[]},\n'
    '  "why_this_score": {"hook_detail":"X","offer_detail":"X","trust_detail":"X","friction_detail":"X","top_3_reasons":["X","X","X"],"critical_gaps":["X"]},\n'
    '  "fix_plan": {"priority_actions":[{"impact":"high","effort":"low","what":"X","how":"X","why":"X"}],"ab_tests":[{"hypothesis":"X","variant_a":"X","variant_b":"X","success_metric":"X"}]},\n'
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

def run_audit(mode, platform, offer_type, landing_content, ad_text, market_context, model):
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

    system = (
        SYSTEM_PROMPT_BASE
        .replace("MARKET_CONTEXT_PLACEHOLDER", market_context)
        .replace("METHODOLOGY_PLACEHOLDER", methodology_context or "Non disponible.")
    )

    # Construire le prompt utilisateur
    user_parts = [
        "AUDIT LRS -- " + mode.upper(),
        "Plateforme : " + platform + " | Offre : " + offer_type,
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

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=0.15,
            max_tokens=3500,
            response_format={"type": "json_object"},
        )
    except Exception as e:
        err = str(e)
        if "api_key" in err.lower() or "authentication" in err.lower():
            raise ValueError("Cle API invalide ou expiree. Verifiez votre OPENAI_API_KEY.")
        if "rate_limit" in err.lower():
            raise ValueError("Rate limit OpenAI atteint. Attendez quelques secondes et relancez.")
        if "quota" in err.lower() or "billing" in err.lower():
            raise ValueError("Quota OpenAI epuise. Verifiez votre solde sur platform.openai.com.")
        raise ValueError("Erreur OpenAI : " + err)

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

    L = ["=" * 60,
         "LRS - LAUNCH RISK SYSTEM V" + APP_VERSION,
         "Audit du " + meta.get("timestamp", ""),
         "=" * 60, "",
         "MODE         : " + meta.get("mode", ""),
         "PLATEFORME   : " + meta.get("platform", ""),
         "TYPE D'OFFRE : " + meta.get("offer_type", ""),
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
    for a in fp.get("priority_actions", []):
        L += ["[" + a.get("impact", "").upper() + " | " + a.get("effort", "").upper() + "]",
              "  Quoi    : " + a.get("what", ""),
              "  Comment : " + a.get("how", ""),
              "  Pourquoi: " + a.get("why", ""), ""]

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
    st.subheader("Resultat LRS")

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Score Global", str(score) + " / 20")
    with col2:
        rc = RISK_COLORS.get(risk, "#888")
        st.markdown("**Risk Level**<br><span style='font-size:1.4em;color:" + rc + ";font-weight:800'>" + risk + "</span>", unsafe_allow_html=True)
    with col3:
        st.markdown("**Launch Decision**<br><span style='font-weight:700'>" + dec + "</span>", unsafe_allow_html=True)
    with col4:
        mc = MATCH_COLORS.get(ms, "#888")
        st.markdown("**Message Match**<br><span style='font-size:1.4em;color:" + mc + ";font-weight:800'>" + ms + "</span>", unsafe_allow_html=True)

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
    for a in fp.get("priority_actions", []):
        imp   = a.get("impact", "medium")
        icon2 = "🔴" if imp == "high" else "🟡" if imp == "medium" else "🟢"
        with st.expander(icon2 + " " + a.get("what", "") + " [" + imp.upper() + " | " + a.get("effort", "").upper() + "]"):
            st.markdown("**Comment :** " + a.get("how", ""))
            st.markdown("**Pourquoi :** " + a.get("why", ""))

    for t in fp.get("ab_tests", []):
        with st.expander("Test : " + t.get("hypothesis", "")):
            ta, tb = st.columns(2)
            with ta: st.markdown("**A :** " + t.get("variant_a", ""))
            with tb: st.markdown("**B :** " + t.get("variant_b", ""))
            st.markdown("**Metrique :** " + t.get("success_metric", ""))

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

            if mode in ("Funnel Only", "Full Risk") and landing_url.strip():
                with st.spinner("Extraction du contenu de la page..."):
                    landing_content, status = extract_page(landing_url.strip())
                st.info(status)
                if not landing_content:
                    st.error("Impossible d'extraire le contenu. Verifiez l'URL.")
                    st.stop()

            with st.spinner("Analyse LRS en cours... (10-30 secondes)"):
                try:
                    result = run_audit(mode, platform, offer_type, landing_content,
                                       ad_text, market_context, model)
                    ts   = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                    meta = {"mode": mode, "platform": platform, "offer_type": offer_type,
                            "url": landing_url, "timestamp": ts}
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

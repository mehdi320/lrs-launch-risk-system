# LRS — Pilote UI Apple-style — serveur local
#
# FastAPI expose la logique d'audit (audit_engine.py) à un frontend custom
# (pilot_static/index.html) pour valider un rendu "Apple-style" avant une
# éventuelle migration complète hors de Streamlit.
#
# Lancer : uvicorn pilot_server:app --port 8600 --reload

import datetime
import os
import secrets as _secrets
import sys
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.sessions import SessionMiddleware

import ads_api
import audit_engine
import email_alerts
import integrations
import resources_content
import user_accounts
from jsonstore import load_json_file, save_json_file

try:
    from lrs_pdf_report import generate_pdf_report
    PDF_AVAILABLE = True
except Exception:
    PDF_AVAILABLE = False


def _get_app_password():
    return os.getenv("APP_PASSWORD", "")


@asynccontextmanager
async def _lifespan(app: FastAPI):
    if not _get_app_password():
        print(
            "\n⚠️  APP_PASSWORD non défini — le pilote démarre en accès libre "
            "(aucune authentification sur /api/*). Acceptable en dev local ; à "
            "ne jamais laisser ainsi sur un déploiement exposé au réseau — voir "
            "DEPLOYMENT.md.\n",
            file=sys.stderr,
        )
    yield


app = FastAPI(title="LRS Pilot", lifespan=_lifespan)


@app.get("/api/health")
def health():
    """Healthcheck pour orchestrateurs/load balancers (Docker HEALTHCHECK,
    plateforme de déploiement...) — ne dépend d'aucune clé API ni d'état."""
    return {"status": "ok"}


_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_STATIC_DIR = os.path.join(_BASE_DIR, "pilot_static")

# Mêmes fichiers que l'app Streamlit (app.py) : le pilote lit/écrit dans le
# même état partagé pour que les deux UIs restent synchronisées.
HISTORY_FILE = os.path.join(_BASE_DIR, ".lrs_history.json")
PROJECTS_FILE = os.path.join(_BASE_DIR, ".lrs_projects.json")
CAMPAIGN_FILE = os.path.join(_BASE_DIR, ".lrs_campaigns.json")
AB_FILE = os.path.join(_BASE_DIR, ".lrs_abtests.json")
SWIPE_FILE = os.path.join(_BASE_DIR, ".lrs_swipefiles.json")
ADS_CREDS_FILE = os.path.join(_BASE_DIR, ".lrs_ads_creds.json")
SCHEDULE_FILE = os.path.join(_BASE_DIR, ".lrs_schedule.json")
ONBOARDING_FILE = os.path.join(_BASE_DIR, ".lrs_onboarded.json")


# ══════════════════════════════════════════════════════════════
# ── Accès par mot de passe (miroir de app.py::check_access) ────
# Un seul mot de passe partagé (pas de comptes multi-utilisateurs — l'app
# Streamlit de référence n'en a pas non plus : l'accès payant se fait via
# un lien d'achat externe qui donne ce mot de passe).
# _get_app_password() est définie plus haut (avant `app = FastAPI(...)`),
# nécessaire dès le lifespan de démarrage.
# ══════════════════════════════════════════════════════════════

@app.middleware("http")
async def _require_auth(request: Request, call_next):
    pwd_required = _get_app_password()
    path = request.url.path
    if not pwd_required or not path.startswith("/api/") or path in ("/api/auth/login", "/api/auth/status", "/api/health"):
        return await call_next(request)
    if request.session.get("authenticated"):
        return await call_next(request)
    return JSONResponse({"detail": "Authentification requise."}, status_code=401)


# Clé de session : fixe si fournie (recommandé en prod pour survivre aux
# redémarrages), sinon générée aléatoirement au démarrage (les sessions
# ouvertes sont invalidées à chaque redémarrage — acceptable pour un pilote).
# https_only=False par défaut pour ne pas casser le dev local (uvicorn parle
# HTTP en clair sans reverse proxy) — mettre APP_HTTPS_ONLY=true dès que le
# pilote tourne derrière un reverse proxy qui termine le TLS (voir
# DEPLOYMENT.md), sinon le cookie de session part aussi sur du HTTP simple.
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("APP_SECRET_KEY") or _secrets.token_hex(32),
    https_only=os.getenv("APP_HTTPS_ONLY", "").strip().lower() in ("1", "true", "yes"),
)
# Compresse les réponses (index.html ~140 Ko non minifié, réponses JSON des
# /api/*) — gain net de bande passante/temps de chargement, aucun coût de
# config côté client (les navigateurs négocient gzip automatiquement).
app.add_middleware(GZipMiddleware, minimum_size=500)


VALID_MODES = ("Funnel Only", "Ads Only", "Full Risk")


def _default_swipes():
    return {"hooks": [], "headlines": [], "ctas": [], "angles": []}


def _load_history():
    return [e for e in load_json_file(HISTORY_FILE, list) if isinstance(e, dict)]


def _auto_save_swipes(result, meta):
    """Alimente automatiquement la librairie swipe files depuis le rewrite
    généré par un audit (headline -> headlines, cta_primary -> ctas)."""
    rw = result.get("rewrite", {})
    if not rw.get("headline") and not rw.get("cta_primary"):
        return
    swipes = load_json_file(SWIPE_FILE, _default_swipes)
    ts = meta.get("timestamp", "")
    score = result.get("_c", {}).get("score", 0)
    if rw.get("headline"):
        swipes.setdefault("headlines", []).insert(0, {
            "text": rw["headline"], "platform": meta.get("platform", ""),
            "offer": meta.get("offer_type", ""), "notes": "", "ts": ts,
            "score_at_save": score, "manual": False,
        })
    if rw.get("cta_primary"):
        swipes.setdefault("ctas", []).insert(0, {
            "text": rw["cta_primary"], "platform": meta.get("platform", ""),
            "offer": meta.get("offer_type", ""), "notes": "", "ts": ts,
            "score_at_save": score, "manual": False,
        })
    save_json_file(SWIPE_FILE, swipes)


def _save_history_entry(result, meta):
    history = _load_history()
    entry = {
        **meta,
        "score": result.get("_c", {}).get("score", 0),
        "decision": result.get("_c", {}).get("decision", ""),
        "result": {k: v for k, v in result.items() if k != "_c"},
    }
    history.insert(0, entry)
    history = history[:50]
    save_json_file(HISTORY_FILE, history)
    _auto_save_swipes(result, meta)


def _reconstruct_c(entry):
    """Reconstruit le dict `_c` (score détaillé) d'une entrée d'historique
    persistée — `_c` est volontairement retiré avant écriture sur disque
    (voir _save_history_entry), donc on le recalcule à la lecture."""
    score = entry.get("score", 0)
    decision, risk = audit_engine.get_decision(score)
    bd = entry.get("result", {}).get("lrs", {}).get("score_breakdown_5", {})
    hook = max(0, min(5, int(bd.get("hook", 0))))
    offer = max(0, min(5, int(bd.get("offer", 0))))
    trust = max(0, min(5, int(bd.get("trust", 0))))
    friction = max(0, min(5, int(bd.get("friction_message_match", 0))))
    tier = audit_engine.get_tier(score)
    offer_type = entry.get("offer_type", "Digital product")
    bench = audit_engine.CVR_BENCHMARKS.get(offer_type, audit_engine.CVR_BENCHMARKS["Digital product"])
    cvr_cur, cvr_fix, cvr_up = bench[tier]
    return {
        "score": score, "hook": hook, "offer": offer, "trust": trust, "friction": friction,
        "decision": decision, "risk": risk,
        "cvr_cur": cvr_cur, "cvr_fix": cvr_fix, "cvr_up": cvr_up,
    }


def _full_result(entry):
    result = dict(entry.get("result", {}))
    result["_c"] = _reconstruct_c(entry)
    return result


class AuditRequest(BaseModel):
    mode: str = "Funnel Only"
    url: str = ""
    ad_text: str = ""
    platform: str = "Meta"
    offer_type: str = "Digital product"
    brand_type: str = "Nouveau lancement"
    model: str = "gpt-4o-mini"


BULK_MAX_URLS = 20


class BulkAuditRequest(BaseModel):
    urls: list[str] = Field(default_factory=list)
    mode: str = "Funnel Only"
    platform: str = "Meta"
    offer_type: str = "Digital product"
    brand_type: str = "Nouveau lancement"
    model: str = "gpt-4o-mini"


class CreativeAnglesRequest(BaseModel):
    offer_description: str = ""
    platform: str = "Meta"
    offer_type: str = "Digital product"
    model: str = "gpt-4o-mini"


@app.post("/api/audit")
def run_audit_endpoint(req: AuditRequest):
    mode = req.mode if req.mode in VALID_MODES else "Funnel Only"
    url = req.url.strip()
    ad_text = req.ad_text.strip()

    if mode in ("Funnel Only", "Full Risk") and not url:
        raise HTTPException(status_code=400, detail="URL de la landing page requise pour ce mode.")
    if mode in ("Ads Only", "Full Risk") and not ad_text:
        raise HTTPException(status_code=400, detail="Texte de la publicité requis pour ce mode.")

    landing_content, status, is_js_page = "", "", False
    page_lang, page_type = "fr", "Non applicable (mode Ads Only)"

    if mode in ("Funnel Only", "Full Risk") and url:
        landing_content, status, is_js_page = audit_engine.extract_page(url)
        if not landing_content:
            raise HTTPException(status_code=422, detail=f"Impossible d'extraire le contenu de la page : {status}")
        page_lang = audit_engine.detect_language(landing_content)
        page_type = audit_engine.detect_page_type(landing_content, url)

    try:
        result = audit_engine.run_audit(
            mode=mode,
            platform=req.platform,
            offer_type=req.offer_type,
            landing_content=landing_content,
            ad_text=ad_text,
            market_context="",
            model=req.model,
            brand_type=req.brand_type,
            page_type=page_type,
            page_lang=page_lang,
        )
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))

    result["_meta"] = {
        "mode": mode,
        "url": url,
        "extraction_status": status,
        "is_js_page": is_js_page,
        "page_type": page_type,
        "page_lang": page_lang,
    }

    meta = {
        "mode": mode,
        "platform": req.platform,
        "offer_type": req.offer_type,
        "url": url,
        "timestamp": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
        "brand_type": req.brand_type,
        "page_type": page_type,
        "ad_text": ad_text,
        "model": req.model,
    }
    _save_history_entry(result, meta)

    return result


@app.get("/api/dashboard")
def get_dashboard():
    history = _load_history()
    all_scores = [e.get("score", 0) for e in history if e.get("score")]

    avg_score = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0
    best_score = max(all_scores) if all_scores else 0
    danger_count = sum(1 for s in all_scores if s <= 9)
    ready_count = sum(1 for s in all_scores if s >= 15)

    today = datetime.date.today()
    checked_days = set()
    for e in history:
        try:
            checked_days.add(datetime.datetime.strptime(e.get("timestamp", ""), "%d/%m/%Y %H:%M").date())
        except Exception:
            pass
    streak_days = 0
    if today in checked_days or (today - datetime.timedelta(days=1)) in checked_days:
        check_day = today if today in checked_days else today - datetime.timedelta(days=1)
        while check_day in checked_days:
            streak_days += 1
            check_day -= datetime.timedelta(days=1)

    next_gap, next_label = 0, ""
    if history:
        latest_score = all_scores[0] if all_scores else 0
        if latest_score <= 9:
            next_thresh, next_label = 10, "Test small budget"
        elif latest_score <= 14:
            next_thresh, next_label = 15, "Ready to scale"
        else:
            next_thresh, next_label = 20, "Score parfait"
        next_gap = max(0, next_thresh - latest_score)

    danger_pages = [
        {
            "label": str(e.get("url") or e.get("offer_type") or "")[:55],
            "score": e.get("score", 0),
            "timestamp": e.get("timestamp", ""),
        }
        for e in history if e.get("score", 20) <= 9
    ][:5]

    recent = list(reversed(history[:10]))
    evolution = [
        {
            "index": i + 1,
            "score": e.get("score", 0),
            "label": str(e.get("url") or e.get("offer_type") or "")[:30],
        }
        for i, e in enumerate(recent)
    ]

    recent_audits = [
        {
            "label": str(e.get("url") or e.get("offer_type") or ""),
            "score": e.get("score", 0),
            "timestamp": e.get("timestamp", ""),
            "mode": e.get("mode", ""),
            "platform": e.get("platform", ""),
            "decision": e.get("decision", ""),
        }
        for e in history[:8]
    ]

    return {
        "total_audits": len(history),
        "avg_score": avg_score,
        "best_score": best_score,
        "danger_count": danger_count,
        "ready_count": ready_count,
        "streak_days": streak_days,
        "next_gap": next_gap,
        "next_label": next_label,
        "danger_pages": danger_pages,
        "evolution": evolution,
        "recent_audits": recent_audits,
    }


@app.get("/api/history")
def get_history(q: str = "", risk: str = "Tous", platform: str = "Toutes"):
    history = _load_history()

    def entry_risk(e):
        return audit_engine.get_decision(e.get("score", 0))[1]

    q_norm = q.strip().lower()
    filtered = []
    for e in history:
        if q_norm:
            haystack = (str(e.get("url", "")) + str(e.get("platform", "")) +
                        str(e.get("offer_type", "")) + str(e.get("score", ""))).lower()
            if q_norm not in haystack:
                continue
        if risk != "Tous" and entry_risk(e) != risk:
            continue
        if platform != "Toutes" and e.get("platform", "") != platform:
            continue
        filtered.append(e)

    entries = []
    for i, e in enumerate(filtered):
        delta = None
        if i + 1 < len(filtered):
            delta = e.get("score", 0) - filtered[i + 1].get("score", 0)
        entries.append({
            "url": e.get("url", ""),
            "offer_type": e.get("offer_type", ""),
            "mode": e.get("mode", ""),
            "platform": e.get("platform", ""),
            "timestamp": e.get("timestamp", ""),
            "score": e.get("score", 0),
            "decision": e.get("decision", ""),
            "risk": entry_risk(e),
            "delta": delta,
        })

    stats = None
    if len(filtered) >= 2:
        first_score = filtered[-1].get("score", 0)
        latest_score = filtered[0].get("score", 0)
        stats = {
            "delta_global": latest_score - first_score,
            "avg_score": round(sum(e.get("score", 0) for e in filtered) / len(filtered), 1),
            "total": len(filtered),
        }

    evolution = [
        {
            "index": i + 1,
            "score": e.get("score", 0),
            "label": str(e.get("url") or e.get("offer_type") or "")[:30],
        }
        for i, e in enumerate(reversed(filtered))
    ]

    return {"entries": entries, "stats": stats, "evolution": evolution}


@app.get("/api/alerts")
def get_alerts():
    history = _load_history()
    if len(history) < 2:
        return {"alerts": []}

    url_map = {}
    for entry in reversed(history):
        url = entry.get("url", "")
        if not url:
            continue
        url_map.setdefault(url, []).append(entry)

    alerts = []
    for url, entries in url_map.items():
        if len(entries) < 2:
            continue
        latest = entries[-1]
        prev = entries[-2]
        delta = latest.get("score", 0) - prev.get("score", 0)
        if abs(delta) >= 2:
            alerts.append({
                "url": url,
                "latest_score": latest.get("score", 0),
                "prev_score": prev.get("score", 0),
                "delta": delta,
                "latest_ts": latest.get("timestamp", ""),
                "direction": "up" if delta > 0 else "down",
            })
    alerts.sort(key=lambda a: abs(a["delta"]), reverse=True)
    return {"alerts": alerts}


@app.post("/api/bulk-audit")
def run_bulk_audit(req: BulkAuditRequest):
    mode = req.mode if req.mode in ("Funnel Only", "Full Risk") else "Funnel Only"
    urls = [u.strip() for u in req.urls if u.strip().startswith("http")][:BULK_MAX_URLS]
    if not urls:
        raise HTTPException(status_code=400, detail="Aucune URL valide fournie.")

    results = []
    for url in urls:
        try:
            content, status, is_js = audit_engine.extract_page(url)
            if not content:
                results.append({"url": url, "error": status, "score": None})
                continue
            page_type = audit_engine.detect_page_type(content, url)
            page_lang = audit_engine.detect_language(content)
            result = audit_engine.run_audit(
                mode=mode,
                platform=req.platform,
                offer_type=req.offer_type,
                landing_content=content,
                ad_text="",
                market_context="",
                model=req.model,
                brand_type=req.brand_type,
                page_type=page_type,
                page_lang=page_lang,
            )
            c = result.get("_c", {})
            meta = {
                "mode": mode,
                "platform": req.platform,
                "offer_type": req.offer_type,
                "url": url,
                "timestamp": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
                "brand_type": req.brand_type,
                "page_type": page_type,
                "ad_text": "",
                "model": req.model,
            }
            _save_history_entry(result, meta)
            results.append({
                "url": url,
                "score": c.get("score", 0),
                "hook": c.get("hook", 0),
                "offer": c.get("offer", 0),
                "trust": c.get("trust", 0),
                "friction": c.get("friction", 0),
                "decision": c.get("decision", ""),
                "risk": c.get("risk", "High"),
                "error": None,
            })
        except ValueError as e:
            results.append({"url": url, "error": str(e)[:120], "score": None})
        except Exception as e:
            results.append({"url": url, "error": str(e)[:120], "score": None})

    results.sort(key=lambda r: (r["score"] is None, -(r["score"] or 0)))
    return {"results": results}


@app.post("/api/creative-angles")
def get_creative_angles(req: CreativeAnglesRequest):
    offer_description = req.offer_description.strip()
    if not offer_description:
        raise HTTPException(status_code=400, detail="Merci de décrire votre offre.")
    try:
        result = audit_engine.generate_creative_angles(
            offer_description=offer_description,
            platform=req.platform,
            offer_type=req.offer_type,
            model=req.model,
        )
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return result


# ══════════════════════════════════════════════════════════════
# ── Comparaison / Audit Concurrents (même opération, cadrage différent) ──
# ══════════════════════════════════════════════════════════════

class CompareRequest(BaseModel):
    url_a: str = ""
    label_a: str = "Page A"
    url_b: str = ""
    label_b: str = "Page B"
    mode: str = "Funnel Only"
    platform: str = "Meta"
    offer_type: str = "Digital product"
    brand_type: str = "Nouveau lancement"
    model: str = "gpt-4o-mini"


@app.post("/api/compare")
def run_compare(req: CompareRequest):
    mode = req.mode if req.mode in ("Funnel Only", "Full Risk") else "Funnel Only"
    url_a, url_b = req.url_a.strip(), req.url_b.strip()
    if not url_a or not url_b:
        raise HTTPException(status_code=400, detail="Les deux URLs sont requises.")

    sides = []
    for url, label in [(url_a, req.label_a or "Page A"), (url_b, req.label_b or "Page B")]:
        content, status, is_js = audit_engine.extract_page(url)
        if not content:
            raise HTTPException(status_code=422, detail=f"{label} : impossible d'extraire le contenu ({status}).")
        page_type = audit_engine.detect_page_type(content, url)
        page_lang = audit_engine.detect_language(content)
        try:
            result = audit_engine.run_audit(
                mode=mode, platform=req.platform, offer_type=req.offer_type,
                landing_content=content, ad_text="", market_context="",
                model=req.model, brand_type=req.brand_type,
                page_type=page_type, page_lang=page_lang,
            )
        except ValueError as e:
            raise HTTPException(status_code=502, detail=f"{label} : {e}")
        meta = {
            "mode": mode, "platform": req.platform, "offer_type": req.offer_type,
            "url": url, "timestamp": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
            "brand_type": req.brand_type, "page_type": page_type, "ad_text": "", "model": req.model,
        }
        _save_history_entry(result, meta)
        sides.append({"label": label, "url": url, "result": result})

    return {"a": sides[0], "b": sides[1]}


# ══════════════════════════════════════════════════════════════
# ── A/B Test Tracker ────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════

@app.get("/api/abtests")
def list_abtests():
    return {"abtests": load_json_file(AB_FILE, dict)}


class ABTestRunRequest(BaseModel):
    name: str = ""
    hypothesis: str = ""
    test_type: str = "page"  # "page" (page de vente) | "advertorial" (article avant redirection)
    url_a: str = ""
    url_b: str = ""
    platform: str = "Meta"
    offer_type: str = "Digital product"
    model: str = "gpt-4o-mini"


@app.post("/api/abtests/run")
def run_abtest(req: ABTestRunRequest):
    name = req.name.strip()
    is_advertorial = req.test_type == "advertorial"
    url_a, url_b = req.url_a.strip(), req.url_b.strip()
    if not name or not url_a or not url_b:
        raise HTTPException(status_code=400, detail="Nom du test et les deux URLs sont requis.")

    variant_results = {}
    for variant, url in [("A", url_a), ("B", url_b)]:
        content, status, is_js = audit_engine.extract_page(url)
        if not content:
            raise HTTPException(status_code=422, detail=f"Variante {variant} : impossible d'extraire le contenu ({status}).")
        page_lang = audit_engine.detect_language(content)
        # Advertorial : force explicitement le page_type plutot que de se fier a
        # detect_page_type(), qui ne connait pas cette categorie et classerait la
        # page comme "Sales Page" — la penalisant a tort sur OFFER/FRICTION pour
        # des elements normalement absents (l'offre est sur la page suivante).
        page_type = "Advertorial" if is_advertorial else audit_engine.detect_page_type(content, url)
        try:
            result = audit_engine.run_audit(
                mode="Funnel Only", platform=req.platform, offer_type=req.offer_type,
                landing_content=content, ad_text="", market_context="",
                model=req.model, page_type=page_type, page_lang=page_lang,
            )
        except ValueError as e:
            raise HTTPException(status_code=502, detail=f"Variante {variant} : {e}")
        variant_results[variant] = result

    ca = variant_results["A"].get("_c", {})
    cb = variant_results["B"].get("_c", {})
    sa, sb = ca.get("score", 0), cb.get("score", 0)
    winner = "B" if sb > sa else "A" if sa > sb else "="

    abtests = load_json_file(AB_FILE, dict)
    ts = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    if name not in abtests:
        abtests[name] = {"name": name, "hypothesis": req.hypothesis, "test_type": req.test_type, "rounds": [], "created": ts}
    crit_keys = ["hook", "offer", "trust", "friction"]
    abtests[name]["rounds"].append({
        "ts": ts, "score_a": sa, "score_b": sb, "winner": winner,
        "crit_a": {k: ca.get(k, 0) for k in crit_keys},
        "crit_b": {k: cb.get(k, 0) for k in crit_keys},
    })
    save_json_file(AB_FILE, abtests)

    return {
        "winner": winner,
        "a": {"score": sa, "decision": ca.get("decision", ""), "crit": {k: ca.get(k, 0) for k in crit_keys}},
        "b": {"score": sb, "decision": cb.get("decision", ""), "crit": {k: cb.get(k, 0) for k in crit_keys}},
        "abtests": abtests,
    }


@app.delete("/api/abtests/{name}")
def delete_abtest(name: str):
    abtests = load_json_file(AB_FILE, dict)
    abtests.pop(name, None)
    save_json_file(AB_FILE, abtests)
    return {"ok": True}


# ══════════════════════════════════════════════════════════════
# ── Projets multi-pages ─────────────────────────────────────────
# ══════════════════════════════════════════════════════════════

@app.get("/api/projects")
def list_projects():
    return {"projects": load_json_file(PROJECTS_FILE, dict)}


class ProjectCreateRequest(BaseModel):
    name: str = ""
    notes: str = ""
    urls: list[str] = Field(default_factory=list)


@app.post("/api/projects")
def create_project(req: ProjectCreateRequest):
    name = req.name.strip()
    urls = [u.strip() for u in req.urls if u.strip()]
    if not name:
        raise HTTPException(status_code=400, detail="Nom du projet requis.")
    if not urls:
        raise HTTPException(status_code=400, detail="Ajoutez au moins une URL.")
    projects = load_json_file(PROJECTS_FILE, dict)
    projects[name] = {
        "name": name, "notes": req.notes.strip(), "urls": urls,
        "created": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
        "audits": {},
    }
    save_json_file(PROJECTS_FILE, projects)
    return {"projects": projects}


@app.delete("/api/projects/{name}")
def delete_project(name: str):
    projects = load_json_file(PROJECTS_FILE, dict)
    projects.pop(name, None)
    save_json_file(PROJECTS_FILE, projects)
    return {"ok": True}


class ProjectAuditRequest(BaseModel):
    mode: str = "Funnel Only"
    platform: str = "Meta"
    offer_type: str = "Digital product"
    brand_type: str = "Nouveau lancement"
    model: str = "gpt-4o-mini"
    only_remaining: bool = True


@app.post("/api/projects/{name}/audit")
def audit_project(name: str, req: ProjectAuditRequest):
    projects = load_json_file(PROJECTS_FILE, dict)
    proj = projects.get(name)
    if not proj:
        raise HTTPException(status_code=404, detail="Projet introuvable.")
    mode = req.mode if req.mode in ("Funnel Only", "Full Risk") else "Funnel Only"
    urls = proj.get("urls", [])
    targets = [u for u in urls if u not in proj.get("audits", {})] if req.only_remaining else urls
    if not targets:
        targets = urls

    errors = []
    for url in targets:
        try:
            content, status, is_js = audit_engine.extract_page(url)
            if not content:
                errors.append({"url": url, "error": status})
                continue
            page_type = audit_engine.detect_page_type(content, url)
            page_lang = audit_engine.detect_language(content)
            result = audit_engine.run_audit(
                mode=mode, platform=req.platform, offer_type=req.offer_type,
                landing_content=content, ad_text="", market_context="",
                model=req.model, brand_type=req.brand_type,
                page_type=page_type, page_lang=page_lang,
            )
            c = result.get("_c", {})
            ts = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            proj["audits"][url] = {"score": c.get("score", 0), "decision": c.get("decision", ""), "timestamp": ts}
            save_json_file(PROJECTS_FILE, projects)
            meta = {
                "mode": mode, "platform": req.platform, "offer_type": req.offer_type,
                "url": url, "timestamp": ts, "brand_type": req.brand_type,
                "page_type": page_type, "ad_text": "", "model": req.model,
            }
            _save_history_entry(result, meta)
        except Exception as e:
            errors.append({"url": url, "error": str(e)[:120]})

    return {"projects": projects, "errors": errors}


# ══════════════════════════════════════════════════════════════
# ── Campagnes en cours (diagnostic croisé stats pub × score LRS) ──
# ══════════════════════════════════════════════════════════════

@app.get("/api/campaigns")
def list_campaigns():
    campaigns = load_json_file(CAMPAIGN_FILE, dict)
    out = {}
    for name, c in campaigns.items():
        diags = ads_api.correlate_stats(
            c.get("lrs_score"),
            c.get("ctr") or None, c.get("cpc") or None, c.get("roas") or None, c.get("cpa") or None,
        )
        out[name] = {**c, "diagnostics": diags}
    return {"campaigns": out}


class CampaignSaveRequest(BaseModel):
    name: str = ""
    platform: str = "Meta"
    budget_daily: float = 0.0
    ctr: float = 0.0
    cpc: float = 0.0
    roas: float = 0.0
    cpa: float = 0.0
    notes: str = ""
    linked_url: str = ""


@app.post("/api/campaigns")
def save_campaign(req: CampaignSaveRequest):
    name = req.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Nom de la campagne requis.")
    campaigns = load_json_file(CAMPAIGN_FILE, dict)
    history = _load_history()

    lrs_score = None
    if req.linked_url:
        for e in history:
            if e.get("url") == req.linked_url:
                lrs_score = e.get("score")
                break

    ts = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    existing = campaigns.get(name, {})
    hist_snaps = existing.get("history_snaps", {})
    snap_key = datetime.datetime.now().strftime("%d/%m/%Y")
    hist_snaps[snap_key] = {"ctr": req.ctr, "cpc": req.cpc, "roas": req.roas, "cpa": req.cpa}

    campaigns[name] = {
        "name": name, "platform": req.platform, "budget_daily": req.budget_daily,
        "ctr": req.ctr, "cpc": req.cpc, "roas": req.roas, "cpa": req.cpa,
        "notes": req.notes, "linked_url": req.linked_url, "lrs_score": lrs_score,
        "updated": ts, "history_snaps": hist_snaps,
    }
    save_json_file(CAMPAIGN_FILE, campaigns)
    return {"campaigns": campaigns}


@app.delete("/api/campaigns/{name}")
def delete_campaign(name: str):
    campaigns = load_json_file(CAMPAIGN_FILE, dict)
    campaigns.pop(name, None)
    save_json_file(CAMPAIGN_FILE, campaigns)
    return {"ok": True}


# ══════════════════════════════════════════════════════════════
# ── Connexion API Pub (Meta Ads / TikTok Ads) ──────────────────
# ══════════════════════════════════════════════════════════════

@app.get("/api/ads-connector/creds")
def get_ads_creds():
    creds = load_json_file(ADS_CREDS_FILE, dict)
    return {
        "meta_configured": bool(creds.get("meta_token") and creds.get("meta_acc_id")),
        "tt_configured": bool(creds.get("tt_token") and creds.get("tt_adv_id")),
        "meta_acc_id": creds.get("meta_acc_id", ""),
        "tt_adv_id": creds.get("tt_adv_id", ""),
    }


class AdsCredsRequest(BaseModel):
    platform: str
    token: str = ""
    account_id: str = ""


@app.post("/api/ads-connector/creds")
def save_ads_creds_endpoint(req: AdsCredsRequest):
    creds = load_json_file(ADS_CREDS_FILE, dict)
    if req.platform == "meta":
        creds["meta_token"] = req.token.strip()
        creds["meta_acc_id"] = req.account_id.strip()
    elif req.platform == "tiktok":
        creds["tt_token"] = req.token.strip()
        creds["tt_adv_id"] = req.account_id.strip()
    else:
        raise HTTPException(status_code=400, detail="Plateforme inconnue.")
    save_json_file(ADS_CREDS_FILE, creds)
    return {"ok": True}


class AdsImportRequest(BaseModel):
    platform: str
    period: str = "last_7d"


@app.post("/api/ads-connector/import")
def import_ads_campaigns(req: AdsImportRequest):
    creds = load_json_file(ADS_CREDS_FILE, dict)
    try:
        if req.platform == "meta":
            token, acc_id = creds.get("meta_token", ""), creds.get("meta_acc_id", "")
            if not token or not acc_id:
                raise HTTPException(status_code=400, detail="Identifiants Meta manquants — enregistrez-les d'abord.")
            camps = ads_api.fetch_meta_campaigns(token, acc_id, req.period)
        elif req.platform == "tiktok":
            token, adv_id = creds.get("tt_token", ""), creds.get("tt_adv_id", "")
            if not token or not adv_id:
                raise HTTPException(status_code=400, detail="Identifiants TikTok manquants — enregistrez-les d'abord.")
            days = {"7": 7, "14": 14, "30": 30}.get(str(req.period), 7)
            camps = ads_api.fetch_tiktok_campaigns(token, adv_id, days)
        else:
            raise HTTPException(status_code=400, detail="Plateforme inconnue.")
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"campaigns": camps}


# ══════════════════════════════════════════════════════════════
# ── Historique : entrée complète (export / tracker) ────────────
# ══════════════════════════════════════════════════════════════

@app.get("/api/history/entry")
def get_history_entry(url: str = "", timestamp: str = ""):
    history = _load_history()
    for e in history:
        if e.get("url") == url and e.get("timestamp") == timestamp:
            return {"meta": e, "result": _full_result(e)}
    raise HTTPException(status_code=404, detail="Audit introuvable.")


# ══════════════════════════════════════════════════════════════
# ── Ressources : Ads Library / Changelog / Benchmark / Swipe Files ──
# ══════════════════════════════════════════════════════════════

@app.get("/api/resources/ads-library")
def get_ads_library():
    return resources_content.ADS_LIBRARY


@app.get("/api/resources/changelog")
def get_changelog():
    return {"versions": resources_content.CHANGELOG_VERSIONS}


@app.get("/api/resources/benchmark")
def get_benchmark():
    return {"intro": resources_content.BENCHMARK_INTRO, "stats": resources_content.BENCHMARK_STATS}


@app.get("/api/resources/benchmark/pdf")
def get_benchmark_pdf():
    path = os.path.join(_BASE_DIR, "assets", "LRS_Benchmark_Report_2025.pdf")
    if os.path.exists(path):
        return FileResponse(path, media_type="application/pdf", filename="LRS_Benchmark_Report_2025.pdf")
    try:
        from generate_benchmark_report import generate as gen_benchmark
        pdf_bytes = gen_benchmark()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rapport temporairement indisponible : {e}")
    return Response(content=pdf_bytes, media_type="application/pdf",
                     headers={"Content-Disposition": "attachment; filename=LRS_Benchmark_Report_2025.pdf"})


@app.get("/api/swipefiles")
def get_swipefiles():
    return load_json_file(SWIPE_FILE, _default_swipes)


class SwipeAddRequest(BaseModel):
    category: str
    text: str = ""
    platform: str = "Tous"
    offer: str = "Tous"
    notes: str = ""


@app.post("/api/swipefiles")
def add_swipefile(req: SwipeAddRequest):
    if req.category not in ("hooks", "headlines", "ctas", "angles"):
        raise HTTPException(status_code=400, detail="Catégorie inconnue.")
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Le texte est vide.")
    swipes = load_json_file(SWIPE_FILE, _default_swipes)
    swipes.setdefault(req.category, []).insert(0, {
        "text": req.text.strip(), "platform": req.platform, "offer": req.offer,
        "notes": req.notes, "ts": datetime.datetime.now().strftime("%d/%m/%Y"),
        "score_at_save": 0, "manual": True,
    })
    save_json_file(SWIPE_FILE, swipes)
    return swipes


@app.delete("/api/swipefiles/{category}/{index}")
def delete_swipefile(category: str, index: int):
    swipes = load_json_file(SWIPE_FILE, _default_swipes)
    items = swipes.get(category, [])
    if 0 <= index < len(items):
        items.pop(index)
        save_json_file(SWIPE_FILE, swipes)
    return swipes


# ══════════════════════════════════════════════════════════════
# ── Export PDF, partage, intégrations, quotas/plans ─────────────
# ══════════════════════════════════════════════════════════════

class ExportPdfRequest(BaseModel):
    result: dict
    meta: dict = Field(default_factory=dict)
    client_name: str = ""
    report_mode: str = ""


@app.post("/api/export/pdf")
def export_pdf(req: ExportPdfRequest):
    if not PDF_AVAILABLE:
        raise HTTPException(status_code=500, detail="Génération PDF indisponible (reportlab non installé).")
    meta = {**req.meta, "version": "3.5"}
    if req.client_name:
        meta["client_name"] = req.client_name
    if req.report_mode:
        meta["report_mode"] = req.report_mode
    try:
        pdf_bytes = generate_pdf_report(req.result, meta)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur génération PDF : {e}")
    fname = "LRS_audit_client.pdf" if req.report_mode == "client" else "LRS_audit.pdf"
    return Response(content=pdf_bytes, media_type="application/pdf",
                     headers={"Content-Disposition": f"attachment; filename={fname}"})


class IntegrationRequest(BaseModel):
    result: dict
    meta: dict = Field(default_factory=dict)


@app.post("/api/integrations/slack")
def notify_slack(req: IntegrationRequest):
    try:
        integrations.send_slack_notification(req.result, req.meta)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"ok": True}


@app.post("/api/integrations/sheets")
def export_sheets_endpoint(req: IntegrationRequest):
    try:
        integrations.export_to_sheets(req.result, req.meta)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"ok": True}


@app.post("/api/integrations/notion")
def export_notion_endpoint(req: IntegrationRequest):
    try:
        integrations.export_to_notion(req.result, req.meta)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"ok": True}


@app.get("/api/integrations/status")
def integrations_status():
    cfg = integrations.get_integration_config()
    return {
        "slack": bool(cfg["slack_webhook"]),
        "sheets": bool(cfg["sheets_creds"] and cfg["sheets_id"]),
        "notion": bool(cfg["notion_token"] and cfg["notion_db"]),
    }


PLAN_LIMITS = {
    "free": {"label": "Free", "audits_per_month": 3, "price": "Gratuit",
             "features": ["Funnel Only", "Historique", "Checklist"]},
    "starter": {"label": "Starter", "audits_per_month": 20, "price": "19€/mois",
                "features": ["Funnel Only", "Monitoring & alertes", "Emails automatiques"]},
    "pro": {"label": "Pro", "audits_per_month": 999, "price": "49€/mois",
            "features": ["Tous les modes", "Bulk audit", "Ads Library", "Intégrations", "API Pub"]},
    "agency": {"label": "Agency", "audits_per_month": 999, "price": "99€/mois",
               "features": ["Tout Pro", "White label", "Multi-clients"]},
}


@app.get("/api/plans")
def get_plans():
    history = _load_history()
    now = datetime.date.today()
    this_month = 0
    for e in history:
        try:
            ts = datetime.datetime.strptime(e.get("timestamp", ""), "%d/%m/%Y %H:%M").date()
            if ts.year == now.year and ts.month == now.month:
                this_month += 1
        except Exception:
            pass
    return {"plans": PLAN_LIMITS, "usage_this_month": this_month}


# ══════════════════════════════════════════════════════════════
# ── Creative Studio réel (Claude + variantes structurées) ──────
# Nécessite ANTHROPIC_API_KEY — échoue proprement sinon (même
# pattern que OPENAI_API_KEY pour l'Audit).
# ══════════════════════════════════════════════════════════════

class StudioGenerateRequest(BaseModel):
    product_name: str = ""
    description: str = ""
    price: float = 0.0
    audience: str = ""
    kind: str = "advertorial"
    framework: str = "PAS"
    model: str = ""


@app.post("/api/creative-studio/generate")
def studio_generate(req: StudioGenerateRequest):
    try:
        from creative_studio.core.variants import Framework, Product, VariantKind
        from creative_studio.core.copy_generation import DEFAULT_MODEL, generate_variant
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Module Creative Studio indisponible : {e}")

    if not req.product_name.strip() or not req.description.strip():
        raise HTTPException(status_code=400, detail="Nom et description du produit requis.")
    try:
        kind = VariantKind(req.kind)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Type de page inconnu : {req.kind}")
    try:
        framework = Framework(req.framework)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Framework inconnu : {req.framework}")

    product = Product(
        name=req.product_name.strip(), description=req.description.strip(),
        price_cents=int(req.price * 100), stripe_payment_link="", audience=req.audience.strip(),
    )
    try:
        variant = generate_variant(product, kind, framework, model=req.model or DEFAULT_MODEL)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erreur génération : {e}")

    copy = variant.copy
    return {
        "headline": copy.headline, "hook": copy.hook,
        "body_sections": copy.body_sections, "cta": copy.cta,
        "framework": framework.value, "kind": kind.value,
    }


# ══════════════════════════════════════════════════════════════
# ── Authentification (mot de passe partagé) ─────────────────────
# ══════════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    password: str = ""


# Anti-brute-force sur /api/auth/login — un seul mot de passe partagé
# protège toute l'API, sans ça il est bruteforçable a un rythme illimité.
# Compteur en memoire (process unique, pas de Redis pour un pilote) : au
# bout de _LOGIN_MAX_ATTEMPTS echecs dans _LOGIN_WINDOW_SECONDS, verrouille
# la source pendant _LOGIN_LOCKOUT_SECONDS. Cle = IP cliente vue par
# uvicorn — derriere un reverse proxy sans en-tete X-Forwarded-For pris en
# compte (volontairement, pour ne pas faire confiance a un en-tete
# falsifiable), toutes les requetes partageront la meme IP proxy : le
# verrou devient alors global plutot que par visiteur, ce qui reste
# conservateur (jamais moins protecteur qu'un verrou par IP).
_LOGIN_MAX_ATTEMPTS = 5
_LOGIN_WINDOW_SECONDS = 60
_LOGIN_LOCKOUT_SECONDS = 60
_login_attempts = {}  # ip -> (fail_count, window_start_ts, locked_until_ts)


def _login_rate_limited(client_ip):
    now = time.time()
    fail_count, window_start, locked_until = _login_attempts.get(client_ip, (0, now, 0))
    if locked_until and now < locked_until:
        return int(locked_until - now)
    if now - window_start > _LOGIN_WINDOW_SECONDS:
        _login_attempts.pop(client_ip, None)
    return 0


def _login_record_failure(client_ip):
    now = time.time()
    fail_count, window_start, _ = _login_attempts.get(client_ip, (0, now, 0))
    if now - window_start > _LOGIN_WINDOW_SECONDS:
        fail_count, window_start = 0, now
    fail_count += 1
    locked_until = now + _LOGIN_LOCKOUT_SECONDS if fail_count >= _LOGIN_MAX_ATTEMPTS else 0
    _login_attempts[client_ip] = (fail_count, window_start, locked_until)


@app.post("/api/auth/login")
def login(req: LoginRequest, request: Request):
    pwd_required = _get_app_password()
    if not pwd_required:
        request.session["authenticated"] = True
        return {"ok": True}

    client_ip = request.client.host if request.client else "unknown"
    retry_after = _login_rate_limited(client_ip)
    if retry_after:
        raise HTTPException(status_code=429, detail=f"Trop de tentatives. Reessayez dans {retry_after}s.")

    if _secrets.compare_digest(req.password, pwd_required):
        _login_attempts.pop(client_ip, None)
        request.session["authenticated"] = True
        return {"ok": True}
    _login_record_failure(client_ip)
    raise HTTPException(status_code=401, detail="Mot de passe invalide.")


@app.get("/api/auth/status")
def auth_status(request: Request):
    pwd_required = _get_app_password()
    return {
        "password_required": bool(pwd_required),
        "authenticated": (not pwd_required) or bool(request.session.get("authenticated")),
    }


@app.post("/api/auth/logout")
def logout(request: Request):
    request.session.clear()
    return {"ok": True}


# ══════════════════════════════════════════════════════════════
# ── Abonnement LRS (lien magique Stripe) ────────────────────────
# Portage de app.py::check_subscription_access() — meme user_accounts.py,
# meme logique de consommation/renvoi de lien. Ajoute la capacite au
# pilote sans changer le comportement d'acces actuel : ces endpoints ne
# sont PAS branches sur _require_auth ci-dessus (qui reste uniquement le
# mot de passe partage). Un frontend qui veut l'appliquer doit appeler
# /api/auth/subscription-status et agir en consequence lui-meme — activer
# un blocage global cote pilote est une decision produit separee (voir
# LRS_APP_URL, qui pointe aujourd'hui vers l'app Streamlit).
# ══════════════════════════════════════════════════════════════

class ConsumeMagicLinkRequest(BaseModel):
    token: str = ""


@app.post("/api/auth/consume-magic-link")
def consume_magic_link(req: ConsumeMagicLinkRequest, request: Request):
    token = req.token.strip()
    if not token:
        raise HTTPException(status_code=400, detail="Token manquant.")
    email = user_accounts.consume_magic_link(token)
    if not email:
        raise HTTPException(status_code=400, detail="Ce lien est invalide ou a expiré.")
    request.session["subscriber_email"] = email
    return {"ok": True, "email": email}


@app.get("/api/auth/subscription-status")
def subscription_status(request: Request):
    email = request.session.get("subscriber_email")
    if not email:
        return {"active": False, "email": None}
    user = user_accounts.get_user(email)
    return {"active": bool(user and user["status"] == "active"), "email": email}


class RequestMagicLinkRequest(BaseModel):
    email: str = ""


@app.post("/api/auth/request-magic-link")
def request_magic_link(req: RequestMagicLinkRequest):
    email_clean = req.email.strip().lower()
    if email_clean and user_accounts.is_valid_email(email_clean):
        user = user_accounts.get_user(email_clean)
        if user and user["status"] == "active":
            # rate_limit=True (défaut) : anti-spam, voir user_accounts.create_magic_link.
            magic_token = user_accounts.create_magic_link(email_clean)
            if magic_token:
                app_url = os.getenv("LRS_APP_URL", "")
                link = f"{app_url}?token={magic_token}" if app_url else f"?token={magic_token}"
                email_alerts.send_magic_link_email(email_clean, link, smtp_config=email_alerts.get_smtp_config())
    # Même message dans tous les cas (email inconnu, inactif, invalide, ou
    # rate-limité) — anti-énumération, voir app.py::_render_subscription_lock_screen.
    return {"ok": True, "message": "Si cet email est associé à un abonnement actif, vous recevrez un lien de connexion sous peu."}


# ══════════════════════════════════════════════════════════════
# ── Onboarding interactif ────────────────────────────────────────
# ══════════════════════════════════════════════════════════════

@app.get("/api/onboarding/status")
def onboarding_status():
    return {"onboarded": os.path.exists(ONBOARDING_FILE)}


@app.post("/api/onboarding/complete")
def onboarding_complete():
    save_json_file(ONBOARDING_FILE, {"done": True, "date": datetime.datetime.now().strftime("%d/%m/%Y")})
    return {"ok": True}


# ══════════════════════════════════════════════════════════════
# ── Monitoring : audits planifiés automatiques ──────────────────
# Pas de scheduler serveur permanent (comme app.py, qui vérifie les audits
# en retard une fois par session Streamlit) : le frontend appelle
# /api/monitoring/check une fois à l'ouverture du pilote.
# ══════════════════════════════════════════════════════════════

@app.get("/api/monitoring/schedule")
def list_schedule():
    schedule = load_json_file(SCHEDULE_FILE, dict)
    now = datetime.datetime.now()
    out = {}
    for sid, sched in schedule.items():
        last_run = sched.get("last_run", "")
        freq = int(sched.get("freq_days", 7))
        next_str = "à la prochaine vérification"
        try:
            if last_run:
                lr_dt = datetime.datetime.strptime(last_run, "%d/%m/%Y %H:%M")
                next_run = lr_dt + datetime.timedelta(days=freq)
                days_left = (next_run - now).days
                if days_left > 0:
                    next_str = f"dans {days_left}j"
        except Exception:
            pass
        out[sid] = {**sched, "next_run_hint": next_str}
    return {"schedule": out}


class ScheduleCreateRequest(BaseModel):
    url: str = ""
    freq_days: int = 7
    mode: str = "Funnel Only"
    platform: str = "Meta"
    offer_type: str = "Digital product"
    brand_type: str = "Nouveau lancement"
    alert_email: str = ""


@app.post("/api/monitoring/schedule")
def create_schedule(req: ScheduleCreateRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL requise.")
    schedule = load_json_file(SCHEDULE_FILE, dict)
    sid = "sc_" + str(int(datetime.datetime.now().timestamp()))
    schedule[sid] = {
        "url": url, "freq_days": req.freq_days, "mode": req.mode,
        "platform": req.platform, "offer_type": req.offer_type, "brand_type": req.brand_type,
        "enabled": True, "last_run": "", "last_score": None, "last_error": "",
        "alert_email": req.alert_email.strip(),
        "created": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
    }
    save_json_file(SCHEDULE_FILE, schedule)
    return {"schedule": schedule}


@app.post("/api/monitoring/schedule/{sid}/toggle")
def toggle_schedule(sid: str):
    schedule = load_json_file(SCHEDULE_FILE, dict)
    if sid not in schedule:
        raise HTTPException(status_code=404, detail="Planification introuvable.")
    schedule[sid]["enabled"] = not schedule[sid].get("enabled", True)
    save_json_file(SCHEDULE_FILE, schedule)
    return {"schedule": schedule}


@app.delete("/api/monitoring/schedule/{sid}")
def delete_schedule(sid: str):
    schedule = load_json_file(SCHEDULE_FILE, dict)
    schedule.pop(sid, None)
    save_json_file(SCHEDULE_FILE, schedule)
    return {"ok": True}


def _run_one_scheduled_audit(sid, sched, schedule):
    """Exécute un audit planifié et met à jour son entrée dans `schedule` (en place)."""
    url = sched.get("url", "")
    now = datetime.datetime.now()
    ts = now.strftime("%d/%m/%Y %H:%M")
    if not url:
        return False
    try:
        content, status, is_js = audit_engine.extract_page(url)
        if not content:
            schedule[sid]["last_error"] = status
            schedule[sid]["last_run"] = ts
            return True
        page_type = audit_engine.detect_page_type(content, url)
        page_lang = audit_engine.detect_language(content)
        result = audit_engine.run_audit(
            mode=sched.get("mode", "Funnel Only"), platform=sched.get("platform", "Meta"),
            offer_type=sched.get("offer_type", "Digital product"),
            landing_content=content, ad_text="", market_context="",
            model="gpt-4o-mini", brand_type=sched.get("brand_type", "Nouveau lancement"),
            page_type=page_type, page_lang=page_lang,
        )
        new_score = result.get("_c", {}).get("score", 0)
        prev_score = schedule[sid].get("last_score")
        meta = {
            "mode": sched.get("mode", "Funnel Only"), "platform": sched.get("platform", "Meta"),
            "offer_type": sched.get("offer_type", "Digital product"), "url": url, "timestamp": ts,
            "brand_type": sched.get("brand_type", "Nouveau lancement"), "page_type": page_type,
            "ad_text": "", "model": "gpt-4o-mini", "scheduled": True,
        }
        _save_history_entry(result, meta)
        schedule[sid]["last_run"] = ts
        schedule[sid]["last_error"] = ""
        schedule[sid]["last_score"] = new_score

        alert_email = sched.get("alert_email", "") or os.getenv("LRS_ALERT_EMAIL", "")
        if alert_email and prev_score is not None:
            drop = new_score - int(prev_score)
            if drop <= -2:
                try:
                    email_alerts.send_score_drop_alert(
                        {**meta, "score": new_score, "decision": result.get("_c", {}).get("decision", "")},
                        int(prev_score), alert_email,
                    )
                except Exception:
                    pass
        return True
    except Exception as e:
        schedule[sid]["last_error"] = str(e)[:200]
        schedule[sid]["last_run"] = ts
        return True


@app.post("/api/monitoring/schedule/{sid}/run")
def run_schedule_now(sid: str):
    schedule = load_json_file(SCHEDULE_FILE, dict)
    sched = schedule.get(sid)
    if not sched:
        raise HTTPException(status_code=404, detail="Planification introuvable.")
    _run_one_scheduled_audit(sid, sched, schedule)
    save_json_file(SCHEDULE_FILE, schedule)
    return {"schedule": schedule}


@app.post("/api/monitoring/check")
def check_due_schedules():
    """Vérifie les audits planifiés en retard et les exécute — équivalent de
    app.py::run_scheduled_audits(), appelé une fois par le frontend à l'ouverture."""
    schedule = load_json_file(SCHEDULE_FILE, dict)
    if not schedule:
        return {"ran": 0}
    now = datetime.datetime.now()
    ran = 0
    for sid, sched in list(schedule.items()):
        if not sched.get("enabled", True):
            continue
        last_run_str = sched.get("last_run", "")
        freq_days = int(sched.get("freq_days", 7))
        try:
            last_run = (datetime.datetime.strptime(last_run_str, "%d/%m/%Y %H:%M")
                        if last_run_str else datetime.datetime(2000, 1, 1))
        except Exception:
            last_run = datetime.datetime(2000, 1, 1)
        if (now - last_run).days < freq_days:
            continue
        if _run_one_scheduled_audit(sid, sched, schedule):
            ran += 1

    if ran:
        save_json_file(SCHEDULE_FILE, schedule)
        digest_email = os.getenv("LRS_DIGEST_EMAIL", "")
        if digest_email and schedule:
            digest_entries = [
                {"url": s.get("url", ""), "score": s.get("last_score", 0), "decision": "", "timestamp": s.get("last_run", "")}
                for s in schedule.values()
            ]
            try:
                email_alerts.send_monitoring_digest(digest_entries, digest_email)
            except Exception:
                pass
    return {"ran": ran, "schedule": schedule}


app.mount("/", StaticFiles(directory=_STATIC_DIR, html=True), name="static")

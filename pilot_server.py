# LRS — Pilote UI Apple-style — serveur local
#
# FastAPI expose la logique d'audit (audit_engine.py) à un frontend custom
# (pilot_static/index.html) pour valider un rendu "Apple-style" avant une
# éventuelle migration complète hors de Streamlit.
#
# Lancer : uvicorn pilot_server:app --port 8600 --reload

import datetime
import json
import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import audit_engine

app = FastAPI(title="LRS Pilot")

_STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pilot_static")

# Même fichier que l'app Streamlit (app.py::HISTORY_FILE) : le pilote lit/écrit
# dans l'historique partagé pour que Dashboard reflète les audits des deux UIs.
HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".lrs_history.json")


VALID_MODES = ("Funnel Only", "Ads Only", "Full Risk")


def _load_history():
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [e for e in data if isinstance(e, dict)]
    except Exception:
        pass
    return []


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
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


class AuditRequest(BaseModel):
    mode: str = "Funnel Only"
    url: str = ""
    ad_text: str = ""
    platform: str = "Meta"
    offer_type: str = "Digital product"
    brand_type: str = "Nouveau lancement"
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


app.mount("/", StaticFiles(directory=_STATIC_DIR, html=True), name="static")

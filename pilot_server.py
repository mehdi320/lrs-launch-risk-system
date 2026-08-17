# LRS — Pilote UI Apple-style — serveur local
#
# FastAPI expose la logique d'audit (audit_engine.py) à un frontend custom
# (pilot_static/index.html) pour valider un rendu "Apple-style" avant une
# éventuelle migration complète hors de Streamlit.
#
# Lancer : uvicorn pilot_server:app --port 8600 --reload

import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import audit_engine

app = FastAPI(title="LRS Pilot")

_STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pilot_static")


class AuditRequest(BaseModel):
    url: str = Field(..., min_length=1)
    platform: str = "Meta"
    offer_type: str = "Digital product"
    brand_type: str = "Nouveau lancement"
    model: str = "gpt-4o-mini"


@app.post("/api/audit")
def run_audit_endpoint(req: AuditRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL requise.")

    landing_content, status, is_js_page = audit_engine.extract_page(url)
    if not landing_content:
        raise HTTPException(status_code=422, detail=f"Impossible d'extraire le contenu de la page : {status}")

    page_lang = audit_engine.detect_language(landing_content)
    page_type = audit_engine.detect_page_type(landing_content, url)

    try:
        result = audit_engine.run_audit(
            mode="Funnel Only",
            platform=req.platform,
            offer_type=req.offer_type,
            landing_content=landing_content,
            ad_text="",
            market_context="",
            model=req.model,
            brand_type=req.brand_type,
            page_type=page_type,
            page_lang=page_lang,
        )
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))

    result["_meta"] = {
        "url": url,
        "extraction_status": status,
        "is_js_page": is_js_page,
        "page_type": page_type,
        "page_lang": page_lang,
    }
    return result


app.mount("/", StaticFiles(directory=_STATIC_DIR, html=True), name="static")

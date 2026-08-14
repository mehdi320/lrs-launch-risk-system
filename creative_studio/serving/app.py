"""Service de diffusion public du module Creative Studio.

Rôle strictement limité à trois choses que Streamlit ne sait pas faire :
- servir la variante assignée à un visiteur (split de trafic stable) ;
- tracker les événements (vue, clic vers paiement) ;
- recevoir le webhook Stripe de confirmation d'achat et le relier à la
  bonne variante via `client_reference_id`.

Lancement : uvicorn creative_studio.serving.app:app --port 8000
"""

from __future__ import annotations

import os
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse

try:
    import stripe
except ImportError:  # dépendance optionnelle tant que le webhook n'est pas utilisé
    stripe = None

from creative_studio.core.variants import Event, EventType, utcnow_iso
from creative_studio.storage.db import init_db
from creative_studio.storage.repository import (
    ABTestRepository,
    AssignmentRepository,
    EventRepository,
    ProductRepository,
    VariantRepository,
)
from creative_studio.serving.bucketing import pick_variant_for_new_visitor
from creative_studio.serving.templates import render_variant_page

VISITOR_COOKIE = "lrs_visitor_id"
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
ALLOW_UNVERIFIED_WEBHOOK = os.environ.get("LRS_CS_ALLOW_UNVERIFIED_WEBHOOK", "").lower() == "true"

app = FastAPI(title="LRS Creative Studio — Serving")

products = ProductRepository()
variants = VariantRepository()
tests = ABTestRepository()
assignments = AssignmentRepository()
events = EventRepository()


@app.on_event("startup")
def _startup() -> None:
    init_db()


def _get_or_create_visitor_id(request: Request) -> tuple[str, bool]:
    """Retourne (visitor_id, is_new). Le cookie fait foi ; sinon on en crée un."""
    existing = request.cookies.get(VISITOR_COOKIE)
    if existing:
        return existing, False
    return uuid.uuid4().hex, True


def _set_visitor_cookie(response, visitor_id: str) -> None:
    response.set_cookie(
        VISITOR_COOKIE,
        visitor_id,
        max_age=60 * 60 * 24 * 90,
        httponly=True,
        samesite="lax",
    )


@app.get("/v/{test_id}", response_class=HTMLResponse)
def serve_variant(test_id: str, request: Request):
    test = tests.get(test_id)
    if test is None:
        return PlainTextResponse("Test introuvable.", status_code=404)

    product = products.get(test.product_id)
    if product is None:
        return PlainTextResponse("Produit introuvable.", status_code=404)

    visitor_id, is_new = _get_or_create_visitor_id(request)
    fallback_variant_id = pick_variant_for_new_visitor(test, visitor_id)
    variant_id = assignments.get_or_assign(
        test_id=test.id,
        visitor_id=visitor_id,
        variant_id_if_new=fallback_variant_id,
        assigned_at=utcnow_iso(),
    )

    variant = variants.get(variant_id)
    if variant is None:
        return PlainTextResponse("Variante introuvable.", status_code=404)

    events.record(
        Event(test_id=test.id, variant_id=variant.id, visitor_id=visitor_id, event_type=EventType.VIEW)
    )

    cta_url = f"/v/{test.id}/go"
    html = render_variant_page(variant, product, cta_url=cta_url)
    response = HTMLResponse(content=html)
    if is_new:
        _set_visitor_cookie(response, visitor_id)
    return response


@app.get("/v/{test_id}/go")
def go_to_payment(test_id: str, request: Request):
    test = tests.get(test_id)
    if test is None:
        return PlainTextResponse("Test introuvable.", status_code=404)

    product = products.get(test.product_id)
    if product is None:
        return PlainTextResponse("Produit introuvable.", status_code=404)

    visitor_id = request.cookies.get(VISITOR_COOKIE)
    if not visitor_id:
        # Visiteur direct sans passage par /v/{test_id} d'abord : on l'assigne à la volée.
        visitor_id = uuid.uuid4().hex
        variant_id = pick_variant_for_new_visitor(test, visitor_id)
    else:
        variant_id = assignments.get_or_assign(
            test_id=test.id,
            visitor_id=visitor_id,
            variant_id_if_new=pick_variant_for_new_visitor(test, visitor_id),
            assigned_at=utcnow_iso(),
        )

    events.record(
        Event(
            test_id=test.id,
            variant_id=variant_id,
            visitor_id=visitor_id,
            event_type=EventType.CLICK_TO_PAYMENT,
        )
    )

    client_reference_id = f"{test.id}:{variant_id}:{visitor_id}"
    separator = "&" if "?" in product.stripe_payment_link else "?"
    redirect_url = f"{product.stripe_payment_link}{separator}client_reference_id={client_reference_id}"

    response = RedirectResponse(url=redirect_url, status_code=302)
    if not request.cookies.get(VISITOR_COOKIE):
        _set_visitor_cookie(response, visitor_id)
    return response


@app.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    if stripe is not None and STRIPE_WEBHOOK_SECRET:
        try:
            event_data = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
        except Exception as exc:  # signature invalide ou payload corrompu
            return PlainTextResponse(f"Webhook invalide: {exc}", status_code=400)
    elif ALLOW_UNVERIFIED_WEBHOOK:
        # Mode dev explicite, sans vérification de signature — n'importe qui
        # peut fabriquer un faux achat. Activé uniquement via opt-in explicite
        # (LRS_CS_ALLOW_UNVERIFIED_WEBHOOK=true), jamais par défaut.
        import json

        event_data = json.loads(payload)
    else:
        return PlainTextResponse(
            "STRIPE_WEBHOOK_SECRET manquant — webhook refusé par défaut. "
            "Pour du dev local sans Stripe réel, définis "
            "LRS_CS_ALLOW_UNVERIFIED_WEBHOOK=true explicitement.",
            status_code=503,
        )

    if event_data.get("type") != "checkout.session.completed":
        return PlainTextResponse("ignoré", status_code=200)

    session = event_data["data"]["object"]
    client_reference_id = session.get("client_reference_id") or ""
    parts = client_reference_id.split(":", 2)
    if len(parts) != 3:
        return PlainTextResponse("client_reference_id absent ou invalide", status_code=200)

    test_id, variant_id, visitor_id = parts
    amount_total = session.get("amount_total")

    events.record(
        Event(
            test_id=test_id,
            variant_id=variant_id,
            visitor_id=visitor_id,
            event_type=EventType.PURCHASE,
            amount_cents=amount_total,
        )
    )
    return PlainTextResponse("ok", status_code=200)

"""Service de diffusion public du module Creative Studio.

Rôle limité à quatre choses que Streamlit ne sait pas faire :
- servir la variante assignée à un visiteur (split de trafic stable) ;
- tracker les événements (vue, clic vers paiement) ;
- recevoir le webhook Stripe de confirmation d'achat funnel et le relier
  à la bonne variante via `client_reference_id` ;
- recevoir le webhook Stripe de l'abonnement bêta LRS (mode="subscription")
  et gérer la Session Checkout correspondante — même endpoint webhook que
  les achats funnel (mêmes secret/config Stripe déjà en place), branché
  sur `session.mode` ; écrit dans user_accounts.py (base séparée du reste
  de Creative Studio, voir sa docstring).

Lancement : uvicorn creative_studio.serving.app:app --port 8000
"""

from __future__ import annotations

import os
import sys
import uuid

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

try:
    import stripe
except ImportError:  # dépendance optionnelle tant que le webhook n'est pas utilisé
    stripe = None

import email_alerts
import user_accounts
from creative_studio.core.variants import Event, EventType, FormSubmission, FormSubmissionSource, utcnow_iso
from creative_studio.storage.db import init_db
from creative_studio.storage.media import MEDIA_DIR, ensure_media_dir
from creative_studio.storage.repository import (
    ABTestRepository,
    AssignmentRepository,
    EventRepository,
    FormSubmissionRepository,
    FunnelRepository,
    FunnelStepElementRepository,
    FunnelStepFormRepository,
    FunnelStepMediaRepository,
    FunnelStepPopupRepository,
    ProductRepository,
    VariantRepository,
)
from creative_studio.serving.bucketing import pick_variant_for_new_visitor
from creative_studio.serving.templates import render_variant_page

VISITOR_COOKIE = "lrs_visitor_id"
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
ALLOW_UNVERIFIED_WEBHOOK = os.environ.get("LRS_CS_ALLOW_UNVERIFIED_WEBHOOK", "").lower() == "true"

# ── Abonnement bêta LRS (distinct des Payment Links funnel ci-dessus) ──
STRIPE_BETA_PRICE_ID = os.environ.get("STRIPE_BETA_PRICE_ID", "")
LRS_APP_URL = os.environ.get("LRS_APP_URL", "http://localhost:8501")
LRS_SALES_PAGE_URL = os.environ.get("LRS_SALES_PAGE_URL", "")

app = FastAPI(title="LRS Creative Studio — Serving")

# Sert les médias uploadés (photos/vidéos attachées à une étape de funnel) —
# le dossier doit exister avant le mount, StaticFiles refuse un dossier absent.
ensure_media_dir()
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

products = ProductRepository()
variants = VariantRepository()
tests = ABTestRepository()
assignments = AssignmentRepository()
events = EventRepository()
funnels = FunnelRepository()
funnel_media = FunnelStepMediaRepository()
funnel_elements = FunnelStepElementRepository()
funnel_forms = FunnelStepFormRepository()
funnel_popups = FunnelStepPopupRepository()
form_submissions = FormSubmissionRepository()


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


def _resolve_next_url(test, variant) -> str:
    """Cible du CTA (et de la redirection après soumission de formulaire) :
    chaîne vers l'étape suivante du funnel si elle existe et a déjà un test
    A/B actif, sinon comportement historique (redirection vers Stripe via
    /go). C'est ce chaînage qui rend le taux de passage entre étapes
    mesurable (core.funnel_analytics) — un funnel partiellement configuré
    (étape suivante sans test) se comporte exactement comme avant."""
    funnel_step = funnels.get_step_by_variant(variant.id)
    if funnel_step is not None:
        next_step = funnels.get_next_step(funnel_step.funnel_id, funnel_step.step_order)
        if next_step is not None:
            next_test = tests.find_by_variant(next_step.variant_id)
            if next_test is not None:
                return f"/v/{next_test.id}"
    return f"/v/{test.id}/go"


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

    # Une variante peut être le maillon d'un funnel (Funnel Builder) — si
    # c'est le cas, ses médias/éléments/formulaire/popup attachés sont
    # inclus dans le rendu ; sinon (variante A/B classique) tout est vide.
    funnel_step = funnels.get_step_by_variant(variant.id)
    step_media = funnel_media.list_by_step(funnel_step.id) if funnel_step else []
    step_elements = funnel_elements.list_by_step(funnel_step.id) if funnel_step else []
    step_form = funnel_forms.get_by_step(funnel_step.id) if funnel_step else None
    step_popup = funnel_popups.get_by_step(funnel_step.id) if funnel_step else None

    cta_url = _resolve_next_url(test, variant)
    html = render_variant_page(
        variant, product, cta_url=cta_url, media=step_media, elements=step_elements,
        form=step_form, popup=step_popup, submit_url=f"/v/{test.id}/submit-form",
    )
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


@app.post("/v/{test_id}/submit-form")
async def submit_form(test_id: str, request: Request):
    """Reçoit la soumission du formulaire multi-étapes d'une page, ou de la
    capture email du popup exit-intent (même endpoint, distingués par le
    champ caché __lrs_source injecté dans le HTML — voir
    serving/templates.py). Enregistre les valeurs (form_submissions),
    déclenche l'événement FORM_SUBMIT (signal pour core.funnel_analytics),
    puis redirige vers l'étape suivante du funnel comme un CTA classique.
    """
    test = tests.get(test_id)
    if test is None:
        return PlainTextResponse("Test introuvable.", status_code=404)

    product = products.get(test.product_id)
    if product is None:
        return PlainTextResponse("Produit introuvable.", status_code=404)

    visitor_id = request.cookies.get(VISITOR_COOKIE)
    if not visitor_id:
        visitor_id = uuid.uuid4().hex
        variant_id = pick_variant_for_new_visitor(test, visitor_id)
    else:
        variant_id = assignments.get_or_assign(
            test_id=test.id,
            visitor_id=visitor_id,
            variant_id_if_new=pick_variant_for_new_visitor(test, visitor_id),
            assigned_at=utcnow_iso(),
        )

    variant = variants.get(variant_id)
    if variant is None:
        return PlainTextResponse("Variante introuvable.", status_code=404)

    form_data = await request.form()
    try:
        source = FormSubmissionSource(form_data.get("__lrs_source", "page"))
    except ValueError:
        source = FormSubmissionSource.PAGE
    values = {k: v for k, v in form_data.items() if k != "__lrs_source"}

    form_submissions.create(
        FormSubmission(
            test_id=test.id, variant_id=variant.id, visitor_id=visitor_id, source=source, values=values,
        )
    )
    events.record(
        Event(test_id=test.id, variant_id=variant.id, visitor_id=visitor_id, event_type=EventType.FORM_SUBMIT)
    )

    response = RedirectResponse(url=_resolve_next_url(test, variant), status_code=302)
    if not request.cookies.get(VISITOR_COOKIE):
        _set_visitor_cookie(response, visitor_id)
    return response


@app.get("/checkout/beta")
def checkout_beta():
    """Redirige vers une Session Checkout Stripe pour l'abonnement bêta LRS
    (plan unique, pas de sélecteur côté client). Session créée côté backend
    (pas un Payment Link statique) pour maîtriser cancel_url : un paiement
    annulé ou abandonné doit ramener vers la page de vente, jamais vers un
    état bloquant dans l'app."""
    if stripe is None or not STRIPE_BETA_PRICE_ID:
        return PlainTextResponse(
            "Paiement indisponible : STRIPE_BETA_PRICE_ID non configuré.", status_code=503
        )
    if not LRS_SALES_PAGE_URL:
        return PlainTextResponse(
            "Paiement indisponible : LRS_SALES_PAGE_URL non configuré "
            "(nécessaire pour le retour en cas d'annulation).",
            status_code=503,
        )
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": STRIPE_BETA_PRICE_ID, "quantity": 1}],
        success_url=f"{LRS_APP_URL}?checkout=success",
        cancel_url=LRS_SALES_PAGE_URL,
    )
    return RedirectResponse(url=session.url, status_code=302)


def _map_stripe_subscription_status(stripe_status: str) -> str:
    return {
        "active": "active",
        "trialing": "active",
        "past_due": "past_due",
        "unpaid": "past_due",
        "canceled": "canceled",
        "incomplete_expired": "canceled",
    }.get(stripe_status or "", "inactive")


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

    event_type = event_data.get("type")

    # ── Abonnement bêta LRS : checkout.session.completed en mode
    # "subscription" (les achats funnel ci-dessous sont en mode "payment"),
    # + le cycle de vie de l'abonnement (mise à jour / résiliation) —
    # écrit dans user_accounts.py, complètement séparé des Event funnel.
    if event_type == "checkout.session.completed":
        session = event_data["data"]["object"]
        if session.get("mode") == "subscription":
            email = (session.get("customer_details") or {}).get("email") or session.get("customer_email")
            customer_id = session.get("customer")
            subscription_id = session.get("subscription")
            if email and customer_id and subscription_id:
                user_accounts.upsert_user_from_checkout(email, customer_id, subscription_id)
                magic_token = user_accounts.create_magic_link(email)
                sent = email_alerts.send_magic_link_email(
                    email, f"{LRS_APP_URL}?token={magic_token}",
                    smtp_config=email_alerts.get_smtp_config(),
                )
                if not sent:
                    # Le compte est bien activé en base malgré l'échec d'envoi —
                    # l'utilisateur peut toujours redemander un lien depuis
                    # l'écran de verrouillage de l'app. Logué pour que
                    # l'opérateur voie un SMTP mal configuré dans ses logs
                    # plutôt que de découvrir un abonné payant bloqué.
                    print(
                        f"[stripe_webhook] Échec d'envoi du lien magique à {email} "
                        f"— vérifier la config SMTP (SMTP_HOST/PORT/USER/PASSWORD).",
                        file=sys.stderr,
                    )
            else:
                print(
                    f"[stripe_webhook] checkout.session.completed (subscription) "
                    f"incomplet — email={bool(email)} customer={bool(customer_id)} "
                    f"subscription={bool(subscription_id)} ; compte non activé.",
                    file=sys.stderr,
                )
            return PlainTextResponse("ok", status_code=200)

        # sinon : achat funnel classique (mode="payment"), logique existante inchangée
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

    if event_type in ("customer.subscription.updated", "customer.subscription.deleted"):
        subscription = event_data["data"]["object"]
        status = "canceled" if event_type == "customer.subscription.deleted" else (
            _map_stripe_subscription_status(subscription.get("status"))
        )
        user_accounts.update_subscription_status(subscription.get("id"), status)
        return PlainTextResponse("ok", status_code=200)

    return PlainTextResponse("ignoré", status_code=200)

# LRS™ — Service Stripe (checkout + webhook)
#
# Service séparé de app.py (Streamlit) car Streamlit n'expose pas de route
# HTTP arbitraire capable de recevoir un webhook Stripe. Lancé avec :
#   uvicorn webhook_server:app --port 8000
#
# Partage la même base SQLite que app.py via user_accounts.py
# (LRS_USERS_DB_PATH doit pointer vers le même fichier des deux côtés).

import os
import smtplib
from email.mime.text import MIMEText

import stripe
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse

import user_accounts

app = FastAPI(title="LRS Stripe Webhook")

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")

STRIPE_PRICE_ID     = os.environ.get("STRIPE_PRICE_ID", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
ALLOW_UNVERIFIED_WEBHOOK = os.environ.get("LRS_ALLOW_UNVERIFIED_WEBHOOK", "false").lower() == "true"
LRS_APP_URL = os.environ.get("LRS_APP_URL", "http://localhost:8501")
CHECKOUT_PLAN = os.environ.get("STRIPE_CHECKOUT_PLAN", "starter")  # plan attribué à l'achat bêta

SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")


def _safe_header(value):
    return str(value).replace("\r", " ").replace("\n", " ").strip()


def _send_magic_link_email(to_email, token):
    if not SMTP_HOST or not SMTP_USER:
        return  # SMTP non configuré : pas d'envoi, le lien reste consultable en DB pour debug
    link = f"{LRS_APP_URL}?magic_token={token}"
    body = (
        f"Bonjour,\n\n"
        f"Voici votre lien de connexion à LRS™ (valable 15 minutes) :\n{link}\n\n"
        f"Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.\n"
    )
    msg = MIMEText(body)
    msg["Subject"] = _safe_header("Votre lien de connexion LRS™")
    msg["From"] = SMTP_USER
    msg["To"] = _safe_header(to_email)
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, to_email, msg.as_string())


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/checkout/beta")
def checkout_beta():
    if not stripe.api_key:
        raise HTTPException(503, "STRIPE_SECRET_KEY non configuré côté serveur.")
    if not STRIPE_PRICE_ID:
        raise HTTPException(503, "STRIPE_PRICE_ID non configuré côté serveur.")
    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
            success_url=f"{LRS_APP_URL}?checkout=success",
            cancel_url=f"{LRS_APP_URL}?checkout=cancel",
        )
    except stripe.error.StripeError as e:
        raise HTTPException(502, f"Erreur Stripe : {e}")
    return RedirectResponse(session.url, status_code=303)


@app.post("/api/request-magic-link")
async def request_magic_link(request: Request):
    body = await request.json()
    email = (body.get("email") or "").strip().lower()
    generic_response = JSONResponse({"status": "ok"})  # ne révèle jamais si l'email existe
    if not user_accounts.is_valid_email(email):
        return generic_response
    user = user_accounts.get_user(email)
    if not user or user.get("status") != "active":
        return generic_response
    token = user_accounts.create_magic_link(email)
    if token:
        try:
            _send_magic_link_email(email, token)
        except Exception:
            pass  # ne jamais exposer une erreur SMTP au client
    return generic_response


def _handle_checkout_completed(data):
    email = (data.get("customer_details") or {}).get("email") or data.get("customer_email")
    if not email or not user_accounts.is_valid_email(email):
        return
    user_accounts.upsert_user_from_checkout(
        email=email,
        plan=CHECKOUT_PLAN,
        stripe_customer_id=data.get("customer"),
        stripe_subscription_id=data.get("subscription"),
        status="active",
    )
    token = user_accounts.create_magic_link(email)
    if token:
        _send_magic_link_email(email, token)


def _handle_subscription_updated(data):
    sub_id = data.get("id")
    status = data.get("status", "")
    plan = CHECKOUT_PLAN if status in ("active", "trialing") else "free"
    user_accounts.update_user_plan_by_subscription(sub_id, plan, status)


def _handle_subscription_deleted(data):
    sub_id = data.get("id")
    user_accounts.update_user_plan_by_subscription(sub_id, "free", "canceled")


_EVENT_HANDLERS = {
    "checkout.session.completed": _handle_checkout_completed,
    "customer.subscription.updated": _handle_subscription_updated,
    "customer.subscription.deleted": _handle_subscription_deleted,
}


@app.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    if STRIPE_WEBHOOK_SECRET:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
        except (ValueError, stripe.error.SignatureVerificationError):
            raise HTTPException(400, "Signature invalide.")
        event = event.to_dict()
    elif ALLOW_UNVERIFIED_WEBHOOK:
        import json
        event = json.loads(payload)
    else:
        raise HTTPException(503, "STRIPE_WEBHOOK_SECRET non configuré.")

    event_id = event.get("id", "")
    event_type = event.get("type", "")

    if not event_id:
        raise HTTPException(400, "Event sans id.")

    if not user_accounts.claim_stripe_event(event_id):
        return {"status": "already_processed"}

    try:
        handler = _EVENT_HANDLERS.get(event_type)
        if handler:
            handler(event.get("data", {}).get("object", {}))
        user_accounts.mark_stripe_event_done(event_id)
    except Exception as e:
        user_accounts.release_stripe_event(event_id)
        raise HTTPException(500, f"Échec de traitement, retry attendu : {e}")

    return {"status": "processed", "type": event_type}

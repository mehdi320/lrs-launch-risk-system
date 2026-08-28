#!/usr/bin/env python3
"""Teste le webhook Stripe étendu (activation + cycle de vie de
l'abonnement LRS) contre une instance locale de
creative_studio.serving.app, sans clé Stripe réelle ni carte bancaire.

Prérequis : lancer le service en mode test AVANT ce script, dans un autre
terminal, DEPUIS LA RACINE DU REPO :

    LRS_CS_ALLOW_UNVERIFIED_WEBHOOK=true \
      uvicorn creative_studio.serving.app:app --port 8000

(LRS_CS_ALLOW_UNVERIFIED_WEBHOOK=true désactive la vérification de
signature Stripe pour ce test local — ne jamais l'activer en production.)

Ce script doit tourner dans le même dossier / même .env que le service
testé (en particulier LRS_USERS_DB_PATH si vous l'avez personnalisé,
sinon les deux utilisent le même fichier par défaut .lrs_users.db).

Usage :
    python3 test_stripe_webhook.py [email de test]

Ceci valide la LOGIQUE du webhook (routage par mode/type d'événement,
écriture en base). Avant la mise en prod, validez aussi la vérification
de signature réelle avec `stripe listen --forward-to
localhost:8000/webhook/stripe` — voir STRIPE_SMTP_SETUP.md.
"""

import json
import sys
import time
import urllib.error
import urllib.request

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import user_accounts

WEBHOOK_URL = "http://127.0.0.1:8000/webhook/stripe"


def post_event(event):
    data = json.dumps(event).encode("utf-8")
    req = urllib.request.Request(
        WEBHOOK_URL, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")
    except urllib.error.URLError as e:
        print(f"❌ Impossible de joindre {WEBHOOK_URL} : {e}")
        print("   → Le service tourne-t-il ? Voir la docstring de ce script pour la commande de lancement.")
        sys.exit(1)


def check_status(email, expected):
    u = user_accounts.get_user(email)
    print("   État en base :", u)
    if not u or u["status"] != expected:
        print(f"❌ Statut attendu \"{expected}\", obtenu {u['status'] if u else None!r}.")
        sys.exit(1)


def main():
    email = sys.argv[1] if len(sys.argv) > 1 else f"test-webhook-{int(time.time())}@example.com"
    customer_id = "cus_test_" + str(int(time.time()))
    subscription_id = "sub_test_" + str(int(time.time()))

    print(f"Email de test : {email}\n")

    print("── 1) checkout.session.completed (mode=subscription) — activation ──")
    status, body = post_event({
        "type": "checkout.session.completed",
        "data": {"object": {
            "mode": "subscription",
            "customer": customer_id,
            "subscription": subscription_id,
            "customer_details": {"email": email},
        }},
    })
    print(f"   HTTP {status} — {body}")
    check_status(email, "active")
    print("✅ Activation OK\n")

    print("── 2) customer.subscription.updated (status=past_due) — échec de paiement récurrent ──")
    status, body = post_event({
        "type": "customer.subscription.updated",
        "data": {"object": {"id": subscription_id, "status": "past_due"}},
    })
    print(f"   HTTP {status} — {body}")
    check_status(email, "past_due")
    print("✅ Synchronisation past_due OK\n")

    print("── 3) customer.subscription.deleted — résiliation ──")
    status, body = post_event({
        "type": "customer.subscription.deleted",
        "data": {"object": {"id": subscription_id, "status": "canceled"}},
    })
    print(f"   HTTP {status} — {body}")
    check_status(email, "canceled")
    print("✅ Résiliation OK\n")

    print("── 4) événement non pertinent (invoice.paid) — doit être ignoré proprement ──")
    status, body = post_event({"type": "invoice.paid", "data": {"object": {}}})
    print(f"   HTTP {status} — {body}")
    if status != 200:
        print("❌ Un événement inconnu devrait renvoyer 200 (\"ignoré\"), pas une erreur.")
        sys.exit(1)
    print("✅ Événement ignoré proprement\n")

    print("Tous les tests sont passés. Rappel : signature non vérifiée dans ce mode —")
    print("testez aussi avec `stripe listen` avant la mise en prod (voir STRIPE_SMTP_SETUP.md).")


if __name__ == "__main__":
    main()

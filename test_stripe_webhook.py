# Tests du webhook Stripe (webhook_server.py) — 6 scénarios :
# activation, mise à jour de statut, résiliation, événement ignoré,
# rejeu d'un event dupliqué, échec puis retry.
#
# Lancer : LRS_ALLOW_UNVERIFIED_WEBHOOK=true LRS_USERS_DB_PATH=/tmp/lrs_test_users.db \
#          python3 -m pytest test_stripe_webhook.py -v
# (ou simplement `python3 test_stripe_webhook.py`, un petit runner est fourni en bas de fichier)

import os
import tempfile

os.environ["LRS_USERS_DB_PATH"] = os.path.join(tempfile.gettempdir(), "lrs_test_users.db")
if os.path.exists(os.environ["LRS_USERS_DB_PATH"]):
    os.remove(os.environ["LRS_USERS_DB_PATH"])
os.environ["LRS_ALLOW_UNVERIFIED_WEBHOOK"] = "true"
os.environ["STRIPE_WEBHOOK_SECRET"] = ""  # forcer le mode non-vérifié pour les tests

import user_accounts
import webhook_server
from fastapi.testclient import TestClient

client = TestClient(webhook_server.app)


def _event(event_id, event_type, obj):
    return {"id": event_id, "type": event_type, "data": {"object": obj}}


def test_checkout_completed_creates_user_and_magic_link():
    resp = client.post("/webhook/stripe", json=_event(
        "evt_1", "checkout.session.completed",
        {"customer_details": {"email": "buyer@example.com"},
         "customer": "cus_1", "subscription": "sub_1"},
    ))
    assert resp.status_code == 200, resp.text
    user = user_accounts.get_user("buyer@example.com")
    assert user is not None
    assert user["plan"] == webhook_server.CHECKOUT_PLAN
    assert user["status"] == "active"


def test_subscription_updated_changes_plan_status():
    resp = client.post("/webhook/stripe", json=_event(
        "evt_2", "customer.subscription.updated",
        {"id": "sub_1", "status": "past_due"},
    ))
    assert resp.status_code == 200, resp.text
    user = user_accounts.get_user("buyer@example.com")
    assert user["status"] == "past_due"
    assert user["plan"] == "free"  # dégradé, pas actif


def test_subscription_deleted_revokes_access():
    resp = client.post("/webhook/stripe", json=_event(
        "evt_3", "customer.subscription.deleted",
        {"id": "sub_1"},
    ))
    assert resp.status_code == 200, resp.text
    user = user_accounts.get_user("buyer@example.com")
    assert user["status"] == "canceled"
    assert user["plan"] == "free"


def test_unhandled_event_type_is_ignored():
    resp = client.post("/webhook/stripe", json=_event(
        "evt_4", "payment_intent.created", {"id": "pi_1"},
    ))
    assert resp.status_code == 200, resp.text
    assert resp.json()["type"] == "payment_intent.created"


def test_duplicate_event_id_is_not_reprocessed():
    user_accounts.upsert_user_from_checkout("dup@example.com", "starter",
                                             stripe_subscription_id="sub_dup")
    ev = _event("evt_5", "customer.subscription.deleted", {"id": "sub_dup"})
    r1 = client.post("/webhook/stripe", json=ev)
    assert r1.status_code == 200 and r1.json()["status"] == "processed"
    user = user_accounts.get_user("dup@example.com")
    assert user["status"] == "canceled"

    # Rejeu : réactive manuellement pour prouver que le 2e appel ne retouche rien
    user_accounts.upsert_user_from_checkout("dup@example.com", "starter",
                                             stripe_subscription_id="sub_dup", status="active")
    r2 = client.post("/webhook/stripe", json=ev)
    assert r2.status_code == 200 and r2.json()["status"] == "already_processed"
    user = user_accounts.get_user("dup@example.com")
    assert user["status"] == "active"  # pas re-traité, donc pas re-annulé


def test_failure_then_retry_with_same_event_id_succeeds():
    original = webhook_server._EVENT_HANDLERS["checkout.session.completed"]
    calls = {"n": 0}

    def flaky(data):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("panne simulée (ex: SMTP down)")
        original(data)

    webhook_server._EVENT_HANDLERS["checkout.session.completed"] = flaky
    try:
        ev = _event("evt_6", "checkout.session.completed",
                     {"customer_details": {"email": "retry@example.com"},
                      "customer": "cus_6", "subscription": "sub_6"})
        r1 = client.post("/webhook/stripe", json=ev)
        assert r1.status_code == 500
        assert user_accounts.get_user("retry@example.com") is None  # pas de compte fantôme

        r2 = client.post("/webhook/stripe", json=ev)  # Stripe retry, même event_id
        assert r2.status_code == 200, r2.text
        assert user_accounts.get_user("retry@example.com") is not None
    finally:
        webhook_server._EVENT_HANDLERS["checkout.session.completed"] = original


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    passed, failed = 0, 0
    for t in tests:
        try:
            t()
            print(f"OK   {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL {t.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    raise SystemExit(1 if failed else 0)

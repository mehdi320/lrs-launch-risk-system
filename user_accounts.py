# LRS — Comptes utilisateurs & statut d'abonnement (Stripe)
#
# Base SQLite dédiée, séparée de .lrs_creative_studio.db : le statut de
# facturation d'un utilisateur n'a pas la même nature que les données de
# tests A/B / funnels de Creative Studio, même si les deux modules vivent
# dans le même repo/produit. Utilisée par :
# - creative_studio/serving/app.py (webhook Stripe) pour activer/mettre à
#   jour un compte à réception d'un événement checkout.session.completed
#   ou customer.subscription.updated/.deleted ;
# - app.py (check_subscription_access) pour lire le statut et gérer les
#   liens magiques de connexion.
#
# Aucune donnée de carte bancaire ici — uniquement l'identifiant Stripe
# (customer/subscription) et un statut, toute la partie paiement reste
# côté Stripe.

from __future__ import annotations

import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

DB_PATH = os.environ.get(
    "LRS_USERS_DB_PATH",
    os.path.join(os.path.dirname(__file__), ".lrs_users.db"),
)

MAGIC_LINK_TTL_MINUTES = 15

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    email                   TEXT PRIMARY KEY,
    plan_id                 TEXT NOT NULL DEFAULT 'beta',
    stripe_customer_id      TEXT,
    stripe_subscription_id  TEXT,
    status                  TEXT NOT NULL DEFAULT 'inactive'
                                CHECK (status IN ('inactive','active','past_due','canceled')),
    date_activation         TEXT,
    updated_at              TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_users_subscription ON users(stripe_subscription_id);

CREATE TABLE IF NOT EXISTS magic_links (
    token       TEXT PRIMARY KEY,
    email       TEXT NOT NULL,
    expires_at  TEXT NOT NULL,
    used_at     TEXT
);
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


@contextmanager
def db_session():
    """Context manager : connexion + commit/rollback automatique."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _row_to_user(row: sqlite3.Row) -> dict:
    return {
        "email": row["email"],
        "plan_id": row["plan_id"],
        "stripe_customer_id": row["stripe_customer_id"],
        "stripe_subscription_id": row["stripe_subscription_id"],
        "status": row["status"],
        "date_activation": row["date_activation"],
        "updated_at": row["updated_at"],
    }


def get_user(email: str) -> dict | None:
    init_db()
    with db_session() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email.strip().lower(),)
        ).fetchone()
    return _row_to_user(row) if row else None


def upsert_user_from_checkout(
    email: str, stripe_customer_id: str, stripe_subscription_id: str, plan_id: str = "beta"
) -> None:
    """Active (ou réactive) un compte à réception d'un checkout.session.completed
    en mode subscription. Idempotent : rejouer le même événement webhook ne
    duplique rien (clé primaire = email)."""
    init_db()
    email = email.strip().lower()
    now = _now_iso()
    with db_session() as conn:
        conn.execute(
            """INSERT INTO users
               (email, plan_id, stripe_customer_id, stripe_subscription_id, status, date_activation, updated_at)
               VALUES (?, ?, ?, ?, 'active', ?, ?)
               ON CONFLICT(email) DO UPDATE SET
                   plan_id=excluded.plan_id,
                   stripe_customer_id=excluded.stripe_customer_id,
                   stripe_subscription_id=excluded.stripe_subscription_id,
                   status='active',
                   updated_at=excluded.updated_at""",
            (email, plan_id, stripe_customer_id, stripe_subscription_id, now, now),
        )


def update_subscription_status(stripe_subscription_id: str, status: str) -> None:
    """Synchronise le statut à réception de customer.subscription.updated/.deleted."""
    if status not in ("inactive", "active", "past_due", "canceled"):
        status = "canceled"
    init_db()
    with db_session() as conn:
        conn.execute(
            "UPDATE users SET status = ?, updated_at = ? WHERE stripe_subscription_id = ?",
            (status, _now_iso(), stripe_subscription_id),
        )


def create_magic_link(email: str) -> str:
    """Crée un token à usage unique (15 min). Ne vérifie pas si l'email a un
    compte actif — cette décision (envoyer l'email ou non) appartient à
    l'appelant, pour éviter l'énumération de comptes à ce niveau."""
    init_db()
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=MAGIC_LINK_TTL_MINUTES)).isoformat()
    with db_session() as conn:
        conn.execute(
            "INSERT INTO magic_links (token, email, expires_at, used_at) VALUES (?, ?, ?, NULL)",
            (token, email.strip().lower(), expires_at),
        )
    return token


def consume_magic_link(token: str) -> str | None:
    """Valide et consomme un token (usage unique). Retourne l'email associé,
    ou None si le token est invalide, expiré, ou déjà utilisé."""
    init_db()
    with db_session() as conn:
        row = conn.execute(
            "SELECT email, expires_at, used_at FROM magic_links WHERE token = ?", (token,)
        ).fetchone()
        if row is None or row["used_at"] is not None:
            return None
        try:
            expires_at = datetime.fromisoformat(row["expires_at"])
        except ValueError:
            return None
        if datetime.now(timezone.utc) > expires_at:
            return None
        conn.execute(
            "UPDATE magic_links SET used_at = ? WHERE token = ?", (_now_iso(), token)
        )
        return row["email"]

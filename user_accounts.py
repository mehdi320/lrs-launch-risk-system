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
import re
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

DB_PATH = os.environ.get(
    "LRS_USERS_DB_PATH",
    os.path.join(os.path.dirname(__file__), ".lrs_users.db"),
)

MAGIC_LINK_TTL_MINUTES = 15

# Anti-spam : si un lien magique non expiré et non utilisé existe déjà pour
# un email, on n'en recrée pas un nouveau (et donc on ne renvoie pas d'email)
# avant ce délai. Protège à la fois le bouton "renvoyer mon lien" (n'importe
# qui peut le spammer avec l'email de quelqu'un d'autre) et un webhook Stripe
# retenté/dupliqué (voir claim_stripe_event ci-dessous pour la protection
# principale contre les doublons de webhook).
MAGIC_LINK_RESEND_COOLDOWN_SECONDS = 60

# Format volontairement strict (pas de RFC 5322 complet) : le but n'est pas
# de valider "tous les emails valides possibles" mais de rejeter tout ce qui
# pourrait servir à une injection d'en-tête SMTP (retour chariot, saut de
# ligne, espaces) avant que la valeur n'atteigne email_alerts.py.
_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_EMAIL_MAX_LEN = 254  # limite RFC 5321


def is_valid_email(email: str) -> bool:
    if not email or len(email) > _EMAIL_MAX_LEN:
        return False
    if any(ch in email for ch in ("\r", "\n", "\t")):
        return False
    return bool(_EMAIL_RE.match(email))


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

-- Déduplication des événements webhook Stripe (Stripe retente un event tant
-- qu'il ne reçoit pas un 200 rapide, et peut aussi le renvoyer manuellement
-- depuis le dashboard). Sans ça, un même achat peut réactiver le compte
-- plusieurs fois et surtout envoyer plusieurs emails de lien de connexion.
CREATE TABLE IF NOT EXISTS processed_stripe_events (
    event_id     TEXT PRIMARY KEY,
    processed_at TEXT NOT NULL
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


def _purge_stale_magic_links(conn: sqlite3.Connection) -> None:
    """Supprime les liens magiques anciens (expirés ou déjà utilisés depuis
    plus de 24h) pour que la table ne grossisse pas indéfiniment. Appelé en
    passant lors de la création d'un lien plutôt que via un cron séparé —
    suffisant vu le volume attendu (bêta à quelques dizaines d'utilisateurs)."""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    conn.execute(
        "DELETE FROM magic_links WHERE expires_at < ? OR (used_at IS NOT NULL AND used_at < ?)",
        (cutoff, cutoff),
    )


def create_magic_link(email: str, *, rate_limit: bool = True) -> str | None:
    """Crée un token à usage unique (15 min). Ne vérifie pas si l'email a un
    compte actif — cette décision (envoyer l'email ou non) appartient à
    l'appelant, pour éviter l'énumération de comptes à ce niveau.

    Anti-spam : si rate_limit=True (par défaut) et qu'un lien non expiré/non
    utilisé a déjà été émis pour cet email il y a moins de
    MAGIC_LINK_RESEND_COOLDOWN_SECONDS, ne crée rien et ne renvoie pas
    d'email — retourne None. L'appelant doit traiter None comme "ne pas
    envoyer d'email" sans distinguer ce cas d'un email inconnu/inactif côté
    utilisateur final (message générique), pour ne pas révéler d'info."""
    init_db()
    email = email.strip().lower()
    now = datetime.now(timezone.utc)
    with db_session() as conn:
        _purge_stale_magic_links(conn)
        if rate_limit:
            recent = conn.execute(
                "SELECT expires_at FROM magic_links "
                "WHERE email = ? AND used_at IS NULL "
                "ORDER BY expires_at DESC LIMIT 1",
                (email,),
            ).fetchone()
            if recent:
                created_at = datetime.fromisoformat(recent["expires_at"]) - timedelta(
                    minutes=MAGIC_LINK_TTL_MINUTES
                )
                if now - created_at < timedelta(seconds=MAGIC_LINK_RESEND_COOLDOWN_SECONDS):
                    return None
        token = secrets.token_urlsafe(32)
        expires_at = (now + timedelta(minutes=MAGIC_LINK_TTL_MINUTES)).isoformat()
        conn.execute(
            "INSERT INTO magic_links (token, email, expires_at, used_at) VALUES (?, ?, ?, NULL)",
            (token, email, expires_at),
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


def claim_stripe_event(event_id: str) -> bool:
    """Marque un événement webhook Stripe comme traité, de façon atomique.

    Retourne True la première fois qu'un event_id donné est vu (l'appelant
    doit alors traiter l'événement), False s'il a déjà été traité (l'appelant
    doit répondre 200 sans rejouer les effets de bord — activation de
    compte, envoi d'email). Stripe retente un webhook tant qu'il ne reçoit
    pas de 2xx rapide, et permet aussi un renvoi manuel depuis le dashboard :
    sans cette déduplication, un même paiement peut déclencher plusieurs
    emails de lien de connexion pour le même client.

    S'appuie sur la contrainte PRIMARY KEY(event_id) : l'INSERT échoue si
    l'event_id existe déjà, ce qui est atomique même avec deux requêtes
    concurrentes (SQLite sérialise les écritures)."""
    init_db()
    with db_session() as conn:
        try:
            conn.execute(
                "INSERT INTO processed_stripe_events (event_id, processed_at) VALUES (?, ?)",
                (event_id, _now_iso()),
            )
        except sqlite3.IntegrityError:
            return False
    return True


def release_stripe_event(event_id: str) -> None:
    """Annule un claim_stripe_event() — à appeler si le traitement de
    l'événement échoue APRÈS avoir été réclamé (ex. exception pendant
    upsert_user_from_checkout ou create_magic_link), pour que le prochain
    retry Stripe du même event_id soit retraité au lieu d'être ignoré comme
    "déjà traité". Sans ça, une activation de compte qui plante en cours de
    route serait définitivement perdue : le claim empêcherait tout retry
    ultérieur de refaire le travail, alors qu'il n'a jamais abouti."""
    init_db()
    with db_session() as conn:
        conn.execute("DELETE FROM processed_stripe_events WHERE event_id = ?", (event_id,))

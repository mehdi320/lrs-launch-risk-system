# LRS™ — Comptes utilisateurs (abonnement Stripe + lien magique)
#
# Base SQLite partagée entre app.py (consultation/consommation) et
# webhook_server.py (écriture depuis les événements Stripe). Un seul fichier,
# ouvert/fermé à chaque appel — volume d'écriture faible, pas besoin de pool.

import os
import re
import sqlite3
import secrets
import smtplib
import datetime
from email.mime.text import MIMEText

DB_PATH = os.environ.get("LRS_USERS_DB_PATH") or os.path.join(
    os.path.dirname(__file__), ".lrs_users.db"
)

MAGIC_LINK_TTL_MINUTES  = 15
MAGIC_LINK_COOLDOWN_SEC = 60

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email):
    return bool(email) and bool(_EMAIL_RE.match(email.strip()))


def _now():
    return datetime.datetime.utcnow().isoformat()


def _conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _conn()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                email                  TEXT PRIMARY KEY,
                plan                   TEXT NOT NULL DEFAULT 'free',
                status                 TEXT NOT NULL DEFAULT 'active',
                stripe_customer_id     TEXT,
                stripe_subscription_id TEXT,
                created_at             TEXT NOT NULL,
                updated_at             TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS magic_links (
                token      TEXT PRIMARY KEY,
                email      TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                used       INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS processed_stripe_events (
                event_id   TEXT PRIMARY KEY,
                status     TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()
    finally:
        conn.close()


init_db()


# ── Users ─────────────────────────────────────────────────────

def get_user(email):
    if not email:
        return None
    conn = _conn()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email.strip().lower(),)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def upsert_user_from_checkout(email, plan, stripe_customer_id=None,
                               stripe_subscription_id=None, status="active"):
    email = email.strip().lower()
    now = _now()
    conn = _conn()
    try:
        existing = conn.execute(
            "SELECT email FROM users WHERE email = ?", (email,)
        ).fetchone()
        if existing:
            conn.execute(
                """UPDATE users SET plan=?, status=?, stripe_customer_id=?,
                   stripe_subscription_id=?, updated_at=? WHERE email=?""",
                (plan, status, stripe_customer_id, stripe_subscription_id, now, email),
            )
        else:
            conn.execute(
                """INSERT INTO users
                   (email, plan, status, stripe_customer_id, stripe_subscription_id,
                    created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (email, plan, status, stripe_customer_id, stripe_subscription_id, now, now),
            )
        conn.commit()
    finally:
        conn.close()


def update_user_plan_by_subscription(stripe_subscription_id, plan, status):
    """Utilisé par les événements customer.subscription.* (pas toujours de checkout associé)."""
    now = _now()
    conn = _conn()
    try:
        conn.execute(
            "UPDATE users SET plan=?, status=?, updated_at=? WHERE stripe_subscription_id=?",
            (plan, status, now, stripe_subscription_id),
        )
        conn.commit()
        return conn.total_changes > 0
    finally:
        conn.close()


# ── Magic links ───────────────────────────────────────────────

def create_magic_link(email):
    """
    Crée un token à usage unique (15 min). Retourne le token, ou None si un
    lien vient déjà d'être envoyé à cette adresse il y a moins de 60s
    (anti-spam sur le renvoi).
    """
    email = email.strip().lower()
    conn = _conn()
    try:
        recent = conn.execute(
            """SELECT created_at FROM magic_links WHERE email = ?
               ORDER BY created_at DESC LIMIT 1""",
            (email,),
        ).fetchone()
        if recent:
            last = datetime.datetime.fromisoformat(recent["created_at"])
            if (datetime.datetime.utcnow() - last).total_seconds() < MAGIC_LINK_COOLDOWN_SEC:
                return None

        token = secrets.token_urlsafe(32)
        now = datetime.datetime.utcnow()
        expires = now + datetime.timedelta(minutes=MAGIC_LINK_TTL_MINUTES)
        conn.execute(
            "INSERT INTO magic_links (token, email, created_at, expires_at, used) "
            "VALUES (?, ?, ?, ?, 0)",
            (token, email, now.isoformat(), expires.isoformat()),
        )
        conn.commit()
        return token
    finally:
        conn.close()


def consume_magic_link(token):
    """
    Valide et consomme un token à usage unique. Retourne l'email ou None.

    Le check (used/expiration) et le marquage used=1 sont faits en une seule
    requête UPDATE ... WHERE used=0 AND expires_at > now, pour que deux
    requêtes concurrentes avec le même token (ex : scanner anti-phishing
    d'un client mail qui pré-charge le lien, puis clic réel de l'utilisateur)
    ne puissent pas toutes les deux "gagner" le token : seule une transaction
    peut faire passer used de 0 à 1, rowcount départage les autres.
    """
    if not token:
        return None
    conn = _conn()
    try:
        now = datetime.datetime.utcnow().isoformat()
        cur = conn.execute(
            "UPDATE magic_links SET used = 1 "
            "WHERE token = ? AND used = 0 AND expires_at > ?",
            (token, now),
        )
        if cur.rowcount != 1:
            conn.rollback()
            return None
        row = conn.execute(
            "SELECT email FROM magic_links WHERE token = ?", (token,)
        ).fetchone()
        conn.commit()
        return row["email"] if row else None
    finally:
        conn.close()


def _safe_header(value):
    return str(value).replace("\r", " ").replace("\n", " ").strip()


def send_magic_link_email(to_email, token, smtp_host, smtp_port, smtp_user,
                           smtp_password, app_url=""):
    """
    Construit et envoie l'email du lien de connexion. Partagé par app.py
    (renvoi manuel depuis l'écran de mot de passe) et webhook_server.py
    (envoi automatique à l'achat) pour ne pas dupliquer la construction du
    message des deux côtés. Ne fait rien (silencieusement) si le SMTP n'est
    pas configuré : le lien reste consultable en DB pour debug, et les deux
    appelants traitent déjà un échec d'envoi comme non bloquant.
    """
    if not smtp_host or not smtp_user:
        return
    link = f"{app_url}?magic_token={token}" if app_url else f"?magic_token={token}"
    body = (
        "Bonjour,\n\n"
        f"Voici votre lien de connexion à LRS™ (valable {MAGIC_LINK_TTL_MINUTES} minutes) :\n{link}\n\n"
        "Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.\n"
    )
    msg = MIMEText(body)
    msg["Subject"] = _safe_header("Votre lien de connexion LRS™")
    msg["From"]    = smtp_user
    msg["To"]      = _safe_header(to_email)
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, to_email, msg.as_string())


# ── Idempotence des webhooks Stripe ──────────────────────────
#
# Pattern claim / release : un event est marqué "processing" *avant* le
# traitement (pour qu'un rejeu concurrent le voie déjà pris), puis "done"
# seulement si le traitement réussit. En cas d'échec, release_stripe_event
# supprime la ligne pour qu'un retry Stripe (même event_id) soit rejoué
# depuis zéro — sinon un paiement pourrait rester silencieusement bloqué.

def claim_stripe_event(event_id):
    """True si cet event vient d'être réservé (pas encore vu ou précédent
    claim abandonné). False s'il est déjà en cours ou déjà traité."""
    conn = _conn()
    try:
        existing = conn.execute(
            "SELECT status FROM processed_stripe_events WHERE event_id = ?",
            (event_id,),
        ).fetchone()
        if existing:
            return False
        conn.execute(
            "INSERT INTO processed_stripe_events (event_id, status, created_at) "
            "VALUES (?, 'processing', ?)",
            (event_id, _now()),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # course concurrente : un autre worker a déjà inséré
    finally:
        conn.close()


def mark_stripe_event_done(event_id):
    conn = _conn()
    try:
        conn.execute(
            "UPDATE processed_stripe_events SET status = 'done' WHERE event_id = ?",
            (event_id,),
        )
        conn.commit()
    finally:
        conn.close()


def release_stripe_event(event_id):
    """Retire le claim après un échec de traitement, pour permettre un retry."""
    conn = _conn()
    try:
        conn.execute(
            "DELETE FROM processed_stripe_events WHERE event_id = ? AND status = 'processing'",
            (event_id,),
        )
        conn.commit()
    finally:
        conn.close()

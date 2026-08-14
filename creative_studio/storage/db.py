"""Connexion SQLite et schéma pour le module Creative Studio.

Mode local (V1) : une seule base de données, un seul tenant implicite
("local"). Chaque table porte quand même une colonne tenant_id dès
maintenant pour éviter une migration de schéma le jour où le module
devient multi-tenant (V2) — voir creative_studio/core/variants.py.
"""

import os
import sqlite3
from contextlib import contextmanager

DEFAULT_TENANT_ID = "local"

DB_PATH = os.environ.get(
    "LRS_CS_DB_PATH",
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".lrs_creative_studio.db"),
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id                  TEXT PRIMARY KEY,
    tenant_id           TEXT NOT NULL DEFAULT 'local',
    name                TEXT NOT NULL,
    description         TEXT NOT NULL,
    price_cents         INTEGER NOT NULL,
    currency            TEXT NOT NULL DEFAULT 'EUR',
    stripe_payment_link TEXT NOT NULL,
    audience            TEXT NOT NULL,
    created_at          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS variants (
    id           TEXT PRIMARY KEY,
    tenant_id    TEXT NOT NULL DEFAULT 'local',
    product_id   TEXT NOT NULL REFERENCES products(id),
    kind         TEXT NOT NULL CHECK (kind IN ('advertorial', 'sales_page')),
    framework    TEXT NOT NULL CHECK (framework IN ('AIDA', 'PAS', 'hormozi')),
    copy_json    TEXT NOT NULL,
    lrs_score    INTEGER,
    status       TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'testing', 'archived')),
    created_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ab_tests (
    id                TEXT PRIMARY KEY,
    tenant_id         TEXT NOT NULL DEFAULT 'local',
    product_id        TEXT NOT NULL REFERENCES products(id),
    name              TEXT NOT NULL,
    status            TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'concluded', 'paused')),
    winner_variant_id TEXT REFERENCES variants(id),
    created_at        TEXT NOT NULL,
    concluded_at      TEXT
);

CREATE TABLE IF NOT EXISTS ab_test_variants (
    test_id    TEXT NOT NULL REFERENCES ab_tests(id),
    variant_id TEXT NOT NULL REFERENCES variants(id),
    weight     REAL NOT NULL DEFAULT 1.0,
    PRIMARY KEY (test_id, variant_id)
);

CREATE TABLE IF NOT EXISTS assignments (
    tenant_id    TEXT NOT NULL DEFAULT 'local',
    test_id      TEXT NOT NULL REFERENCES ab_tests(id),
    visitor_id   TEXT NOT NULL,
    variant_id   TEXT NOT NULL REFERENCES variants(id),
    assigned_at  TEXT NOT NULL,
    PRIMARY KEY (test_id, visitor_id)
);

CREATE TABLE IF NOT EXISTS events (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id    TEXT NOT NULL DEFAULT 'local',
    test_id      TEXT NOT NULL REFERENCES ab_tests(id),
    variant_id   TEXT NOT NULL REFERENCES variants(id),
    visitor_id   TEXT NOT NULL,
    event_type   TEXT NOT NULL CHECK (event_type IN ('view', 'click_to_payment', 'purchase')),
    amount_cents INTEGER,
    ts           TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_variant ON events(variant_id, event_type);
CREATE INDEX IF NOT EXISTS idx_events_test ON events(test_id, event_type);

CREATE TABLE IF NOT EXISTS test_results (
    test_id           TEXT NOT NULL REFERENCES ab_tests(id),
    variant_id        TEXT NOT NULL REFERENCES variants(id),
    exposures         INTEGER NOT NULL,
    conversions       INTEGER NOT NULL,
    conversion_rate   REAL NOT NULL,
    p_value           REAL,
    is_significant    INTEGER NOT NULL DEFAULT 0,
    is_winner         INTEGER NOT NULL DEFAULT 0,
    computed_at       TEXT NOT NULL,
    PRIMARY KEY (test_id, variant_id, computed_at)
);

CREATE TABLE IF NOT EXISTS email_sequences (
    id          TEXT PRIMARY KEY,
    tenant_id   TEXT NOT NULL DEFAULT 'local',
    product_id  TEXT NOT NULL REFERENCES products(id),
    angle       TEXT NOT NULL,
    length      INTEGER NOT NULL CHECK (length IN (5, 7, 14)),
    emails_json TEXT NOT NULL,
    created_at  TEXT NOT NULL
);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
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
    """Context manager: connexion + commit/rollback automatique."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

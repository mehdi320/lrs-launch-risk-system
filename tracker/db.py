"""
db.py — Initialisation et accès à la base SQLite locale.
"""

import sqlite3
import logging
from pathlib import Path

DB_PATH = Path(__file__).parent / "tracker.db"

logger = logging.getLogger(__name__)


def get_connection() -> sqlite3.Connection:
    """Retourne une connexion SQLite avec row_factory activé."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # performances en lecture concurrente
    return conn


def init_db() -> None:
    """Crée les tables si elles n'existent pas encore."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS ad_spend (
                date            TEXT NOT NULL,
                campaign_id     TEXT NOT NULL,
                campaign_name   TEXT,
                adset_id        TEXT NOT NULL,
                adset_name      TEXT,
                ad_id           TEXT NOT NULL,
                ad_name         TEXT,
                spend           REAL DEFAULT 0,
                impressions     INTEGER DEFAULT 0,
                clicks          INTEGER DEFAULT 0,
                meta_purchases  REAL DEFAULT 0,
                meta_revenue    REAL DEFAULT 0,
                synced_at       TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (date, ad_id)
            );

            CREATE TABLE IF NOT EXISTS sales (
                sale_id         TEXT PRIMARY KEY,
                email           TEXT,
                amount          REAL NOT NULL,
                currency        TEXT DEFAULT 'EUR',
                utm_source      TEXT,
                utm_campaign    TEXT,
                utm_medium      TEXT,
                utm_content     TEXT,
                utm_term        TEXT,
                created_at      TEXT NOT NULL,
                raw_payload     TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_sales_utm_content
                ON sales (utm_content);

            CREATE INDEX IF NOT EXISTS idx_sales_created_at
                ON sales (created_at);

            CREATE INDEX IF NOT EXISTS idx_spend_date
                ON ad_spend (date);
        """)
        logger.info("Base de données initialisée : %s", DB_PATH)


if __name__ == "__main__":
    init_db()
    print(f"Base initialisée → {DB_PATH}")

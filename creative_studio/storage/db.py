"""Connexion SQLite et schéma pour le module Creative Studio.

Mode local (V1) : une seule base de données, un seul tenant implicite
("local"). Chaque table porte quand même une colonne tenant_id dès
maintenant pour éviter une migration de schéma le jour où le module
devient multi-tenant (V2) — voir creative_studio/core/variants.py.
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Callable

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
    id               TEXT PRIMARY KEY,
    tenant_id        TEXT NOT NULL DEFAULT 'local',
    product_id       TEXT NOT NULL REFERENCES products(id),
    kind             TEXT NOT NULL CHECK (kind IN ('advertorial', 'sales_page')),
    framework        TEXT NOT NULL CHECK (framework IN ('AIDA', 'PAS', 'hormozi')),
    copy_json        TEXT NOT NULL,
    lrs_score        INTEGER,
    status           TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'testing', 'archived', 'killed')),
    source_mode      TEXT NOT NULL DEFAULT 'from_scratch' CHECK (source_mode IN ('from_scratch', 'optimize_existing')),
    varied_dimension TEXT CHECK (varied_dimension IN ('hook', 'social_proof', 'urgency', 'cta')),
    created_at       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ab_tests (
    id                TEXT PRIMARY KEY,
    tenant_id         TEXT NOT NULL DEFAULT 'local',
    product_id        TEXT NOT NULL REFERENCES products(id),
    name              TEXT NOT NULL,
    status            TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'concluded', 'paused')),
    winner_variant_id TEXT REFERENCES variants(id),
    conclusion_reason TEXT CHECK (conclusion_reason IN ('statistical_significance', 'budget_stop_loss')),
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
    alpha_used        REAL NOT NULL DEFAULT 0.05,
    n_looks           INTEGER NOT NULL DEFAULT 1,
    computed_at       TEXT NOT NULL,
    PRIMARY KEY (test_id, variant_id, computed_at)
);

CREATE TABLE IF NOT EXISTS funnels (
    id               TEXT PRIMARY KEY,
    tenant_id        TEXT NOT NULL DEFAULT 'local',
    product_id       TEXT NOT NULL REFERENCES products(id),
    objective        TEXT NOT NULL CHECK (objective IN ('direct_sale', 'email_capture', 'booking')),
    angle            TEXT NOT NULL,
    tone             TEXT NOT NULL,
    promise          TEXT NOT NULL,
    source_reference TEXT,
    created_at       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS funnel_steps (
    id          TEXT PRIMARY KEY,
    tenant_id   TEXT NOT NULL DEFAULT 'local',
    funnel_id   TEXT NOT NULL REFERENCES funnels(id),
    variant_id  TEXT NOT NULL REFERENCES variants(id),
    step_order  INTEGER NOT NULL,
    created_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_funnel_steps_funnel ON funnel_steps(funnel_id, step_order);

CREATE TABLE IF NOT EXISTS funnel_step_media (
    id           TEXT PRIMARY KEY,
    tenant_id    TEXT NOT NULL DEFAULT 'local',
    step_id      TEXT NOT NULL REFERENCES funnel_steps(id),
    media_type   TEXT NOT NULL CHECK (media_type IN ('image', 'video')),
    source_type  TEXT NOT NULL CHECK (source_type IN ('upload', 'url')),
    location     TEXT NOT NULL,
    placement    TEXT NOT NULL DEFAULT 'hero' CHECK (placement IN ('hero', 'proof', 'demo')),
    created_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_funnel_step_media_step ON funnel_step_media(step_id);

-- Pas de CHECK sur element_type : l'ensemble des types est volontairement
-- ouvert (voir core/funnel_elements.py) pour ajouter un nouvel élément de
-- conversion sans migration de schéma.
CREATE TABLE IF NOT EXISTS funnel_step_elements (
    id           TEXT PRIMARY KEY,
    tenant_id    TEXT NOT NULL DEFAULT 'local',
    step_id      TEXT NOT NULL REFERENCES funnel_steps(id),
    element_type TEXT NOT NULL,
    config_json  TEXT NOT NULL,
    enabled      INTEGER NOT NULL DEFAULT 1,
    created_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_funnel_step_elements_step ON funnel_step_elements(step_id);

CREATE TABLE IF NOT EXISTS funnel_step_forms (
    id          TEXT PRIMARY KEY,
    tenant_id   TEXT NOT NULL DEFAULT 'local',
    step_id     TEXT NOT NULL UNIQUE REFERENCES funnel_steps(id),
    screens_json TEXT NOT NULL,
    enabled     INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS funnel_step_popups (
    id          TEXT PRIMARY KEY,
    tenant_id   TEXT NOT NULL DEFAULT 'local',
    step_id     TEXT NOT NULL UNIQUE REFERENCES funnel_steps(id),
    mode        TEXT NOT NULL CHECK (mode IN ('offer', 'email_capture')),
    copy_json   TEXT NOT NULL,
    enabled     INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS form_submissions (
    id           TEXT PRIMARY KEY,
    tenant_id    TEXT NOT NULL DEFAULT 'local',
    test_id      TEXT NOT NULL REFERENCES ab_tests(id),
    variant_id   TEXT NOT NULL REFERENCES variants(id),
    visitor_id   TEXT NOT NULL,
    source       TEXT NOT NULL CHECK (source IN ('page', 'exit_popup')),
    values_json  TEXT NOT NULL,
    submitted_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_form_submissions_test ON form_submissions(test_id, variant_id);

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


# Colonnes ajoutées après la création initiale du schéma — appliquées via
# ALTER TABLE pour les bases locales déjà existantes (CREATE TABLE IF NOT
# EXISTS ne touche pas une table déjà créée). Idempotent : les erreurs
# "duplicate column" sont ignorées.
_MIGRATIONS = [
    "ALTER TABLE ab_tests ADD COLUMN conclusion_reason TEXT",
    "ALTER TABLE test_results ADD COLUMN alpha_used REAL NOT NULL DEFAULT 0.05",
    "ALTER TABLE test_results ADD COLUMN n_looks INTEGER NOT NULL DEFAULT 1",
    "ALTER TABLE variants ADD COLUMN source_mode TEXT NOT NULL DEFAULT 'from_scratch'",
    "ALTER TABLE variants ADD COLUMN varied_dimension TEXT",
    "ALTER TABLE funnels ADD COLUMN source_reference TEXT",
]


def _rebuild_variants_widen_constraints(conn: sqlite3.Connection) -> None:
    """Élargit les CHECK constraints de variants.kind (Funnel Builder :
    capture/booking/confirmation/upsell) et variants.source_mode
    (funnel_builder). SQLite ne supporte pas ALTER TABLE ... DROP CONSTRAINT
    ni ALTER COLUMN sur un CHECK existant — la seule façon de l'élargir est
    de reconstruire la table (rename -> create -> copy -> drop), documentée
    ici comme "migration lourde" par opposition aux ALTER TABLE ADD COLUMN
    simples de _MIGRATIONS ci-dessus.

    Les tables qui référencent variants(id) via un FOREIGN KEY (ab_test_variants,
    assignments, events, test_results, ab_tests.winner_variant_id) ne sont pas
    touchées : seules leurs contraintes déclaratives pointent vers ce nom de
    table, pas des identifiants internes SQLite, donc elles restent valides
    après le rename/recreate tant que le nom final est bien "variants" et que
    foreign_keys est désactivé pendant l'opération.
    """
    conn.execute(
        """CREATE TABLE variants_new (
            id               TEXT PRIMARY KEY,
            tenant_id        TEXT NOT NULL DEFAULT 'local',
            product_id       TEXT NOT NULL REFERENCES products(id),
            kind             TEXT NOT NULL CHECK (kind IN (
                                 'advertorial', 'sales_page', 'capture', 'booking',
                                 'confirmation', 'upsell'
                             )),
            framework        TEXT NOT NULL CHECK (framework IN ('AIDA', 'PAS', 'hormozi')),
            copy_json        TEXT NOT NULL,
            lrs_score        INTEGER,
            status           TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'testing', 'archived', 'killed')),
            source_mode      TEXT NOT NULL DEFAULT 'from_scratch' CHECK (source_mode IN (
                                 'from_scratch', 'optimize_existing', 'funnel_builder'
                             )),
            varied_dimension TEXT CHECK (varied_dimension IN ('hook', 'social_proof', 'urgency', 'cta')),
            created_at       TEXT NOT NULL
        )"""
    )
    conn.execute(
        """INSERT INTO variants_new
           (id, tenant_id, product_id, kind, framework, copy_json, lrs_score,
            status, source_mode, varied_dimension, created_at)
           SELECT id, tenant_id, product_id, kind, framework, copy_json, lrs_score,
                  status, source_mode, varied_dimension, created_at
           FROM variants"""
    )
    conn.execute("DROP TABLE variants")
    conn.execute("ALTER TABLE variants_new RENAME TO variants")


def _rebuild_events_widen_constraint(conn: sqlite3.Connection) -> None:
    """Élargit events.event_type pour accepter 'form_submit' (formulaire
    multi-étapes / popup exit-intent complété) — même contrainte, même
    procédure de reconstruction que _rebuild_variants_widen_constraints."""
    conn.execute(
        """CREATE TABLE events_new (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id    TEXT NOT NULL DEFAULT 'local',
            test_id      TEXT NOT NULL REFERENCES ab_tests(id),
            variant_id   TEXT NOT NULL REFERENCES variants(id),
            visitor_id   TEXT NOT NULL,
            event_type   TEXT NOT NULL CHECK (event_type IN (
                             'view', 'click_to_payment', 'purchase', 'form_submit'
                         )),
            amount_cents INTEGER,
            ts           TEXT NOT NULL
        )"""
    )
    conn.execute(
        """INSERT INTO events_new
           (id, tenant_id, test_id, variant_id, visitor_id, event_type, amount_cents, ts)
           SELECT id, tenant_id, test_id, variant_id, visitor_id, event_type, amount_cents, ts
           FROM events"""
    )
    conn.execute("DROP TABLE events")
    conn.execute("ALTER TABLE events_new RENAME TO events")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_variant ON events(variant_id, event_type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_test ON events(test_id, event_type)")


# Migrations qui ne peuvent pas s'exprimer comme un simple ALTER TABLE ADD
# COLUMN (ex: élargir un CHECK) — chacune tourne exactement une fois, suivie
# via la table schema_migrations plutôt que par un test ad hoc sur le SQL
# existant de la table.
_HEAVY_MIGRATIONS: list[tuple[int, Callable[[sqlite3.Connection], None]]] = [
    (1, _rebuild_variants_widen_constraints),
    (2, _rebuild_events_widen_constraint),
]


def _run_heavy_migrations() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        # PRAGMA foreign_keys ne peut être changé qu'en dehors d'une
        # transaction active — cette connexion est fraîche, rien n'a encore
        # commencé, donc c'est sûr ici. Désactivé le temps du rebuild pour
        # ne pas déclencher de vérification de clé étrangère sur le DROP
        # TABLE variants pendant que d'autres tables la référencent encore.
        conn.execute("PRAGMA foreign_keys=OFF")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
        )
        applied = {row["version"] for row in conn.execute("SELECT version FROM schema_migrations").fetchall()}
        for version, migration_fn in _HEAVY_MIGRATIONS:
            if version in applied:
                continue
            migration_fn(conn)
            conn.execute(
                "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                (version, datetime.now(timezone.utc).isoformat()),
            )
        conn.commit()
    finally:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.close()


def init_db() -> None:
    conn = get_connection()
    try:
        conn.executescript(SCHEMA)
        for statement in _MIGRATIONS:
            try:
                conn.execute(statement)
            except sqlite3.OperationalError:
                pass  # colonne déjà présente
        conn.commit()
    finally:
        conn.close()
    _run_heavy_migrations()


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

-- Baseline — .lrs_creative_studio.db
-- Généré le 2026-09-23 à partir de creative_studio/storage/db.py (SCHEMA)
-- + l'état final des deux migrations lourdes déjà appliquées
-- (_rebuild_variants_widen_constraints, _rebuild_events_widen_constraint) :
-- les CHECK de variants.kind, variants.source_mode et events.event_type
-- ci-dessous reflètent donc l'état RÉEL actuel, pas le texte d'origine de
-- SCHEMA (qui, lui, ne contient que les contraintes initiales — l'élargir
-- au démarrage est le rôle de _HEAVY_MIGRATIONS, voir db.py:296-331).
--
-- Snapshot pour revue uniquement — voir migrations/README.md. Rien ici
-- n'est exécuté par l'application ni par un outil de migration.

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
    event_type   TEXT NOT NULL CHECK (event_type IN (
                     'view', 'click_to_payment', 'purchase', 'form_submit'
                 )),
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

CREATE TABLE IF NOT EXISTS schema_migrations (
    version     INTEGER PRIMARY KEY,
    applied_at  TEXT NOT NULL
);

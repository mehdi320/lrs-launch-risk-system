-- Baseline — .lrs_users.db
-- Généré le 2026-09-23 à partir de user_accounts.py (SCHEMA).
--
-- Snapshot pour revue uniquement — voir migrations/README.md. Rien ici
-- n'est exécuté par l'application ni par un outil de migration. Aucun
-- mécanisme de migration versionnée n'existe encore pour cette base
-- (contrairement à .lrs_creative_studio.db, voir
-- migrations/creative_studio/0001_baseline.sql) — à créer le jour où ce
-- schéma devra évoluer.

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

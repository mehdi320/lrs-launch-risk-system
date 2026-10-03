-- .lrs_users.db
-- Ajoute l'index manquant sur magic_links.email, filtré dans
-- user_accounts.py::create_magic_link (anti-spam) sans index dédié
-- (audit sécurité 2026-09-23, point 11). Appliqué en pratique via
-- SCHEMA (user_accounts.py). Snapshot pour revue uniquement, voir
-- migrations/README.md.

CREATE INDEX IF NOT EXISTS idx_magic_links_email ON magic_links(email);

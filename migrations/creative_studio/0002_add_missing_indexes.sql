-- .lrs_creative_studio.db
-- Ajoute les index manquants sur les colonnes de clé étrangère filtrées
-- dans creative_studio/storage/repository.py sans index dédié (audit
-- sécurité 2026-09-23, point 11). Appliqué en pratique via SCHEMA
-- (creative_studio/storage/db.py) — CREATE INDEX IF NOT EXISTS est
-- rétroactif et sans effet si déjà présent, donc pas besoin d'un
-- _MIGRATIONS séparé pour ça. Snapshot pour revue uniquement, voir
-- migrations/README.md.

CREATE INDEX IF NOT EXISTS idx_products_tenant ON products(tenant_id);
CREATE INDEX IF NOT EXISTS idx_variants_product ON variants(product_id);
CREATE INDEX IF NOT EXISTS idx_ab_tests_product ON ab_tests(product_id);
CREATE INDEX IF NOT EXISTS idx_funnels_product ON funnels(product_id);
CREATE INDEX IF NOT EXISTS idx_email_sequences_product ON email_sequences(product_id);

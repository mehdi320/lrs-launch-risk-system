# Migrations — fichiers de référence

Audit sécurité 2026-09-23, point 13 ("Aucune migration, schéma modifié
directement sur main"). Ces fichiers **ne sont exécutés par rien** — ils
ne sont ni lus au démarrage de l'app, ni par un outil de migration tiers.
Ils existent pour une seule raison : donner à ce schéma une trace
relisible et versionnée indépendamment du code Python, pour qu'un
changement de structure de données puisse être revu comme n'importe quel
autre diff avant d'être répercuté dans le code applicatif.

## Ce qui gère réellement le schéma aujourd'hui

Rien ici ne remplace ni ne modifie ce mécanisme — ces fichiers sont un
instantané en plus, pas une nouvelle source de vérité :

- **`creative_studio/storage/db.py`** — le plus abouti des deux : un
  vrai système de migrations versionnées. `SCHEMA` (création initiale,
  idempotente via `CREATE TABLE IF NOT EXISTS`), `_MIGRATIONS` (ajouts de
  colonnes simples via `ALTER TABLE`, ré-exécutés sans effet si déjà
  appliqués), et `_HEAVY_MIGRATIONS` (reconstructions de table pour les
  changements qu'un simple `ALTER TABLE` ne sait pas faire en SQLite —
  élargir un `CHECK` par exemple), suivies dans une table
  `schema_migrations` pour ne jamais rejouer deux fois la même migration
  lourde. Tout ça tourne automatiquement à chaque démarrage de l'app
  (`init_db()`).
- **`user_accounts.py`** — plus simple : uniquement `CREATE TABLE IF NOT
  EXISTS` (`SCHEMA`, exécuté par `init_db()`). Aucune évolution de schéma
  n'a encore été nécessaire depuis la création de ces tables, donc aucun
  mécanisme de migration n'existe encore ici — le jour où une colonne
  devra être ajoutée, il faudra soit y répliquer le pattern
  `_MIGRATIONS` de `db.py`, soit adopter un outil dédié (Alembic ou
  équivalent).

## Contenu de ce dossier

- `creative_studio/0001_baseline.sql` — snapshot du schéma actuel de
  `.lrs_creative_studio.db`, tel que produit par `SCHEMA` +
  `_HEAVY_MIGRATIONS` appliquées (état final, pas l'historique
  incrémental).
- `user_accounts/0001_baseline.sql` — snapshot du schéma actuel de
  `.lrs_users.db`.

## Pour la suite

Un vrai changement de schéma (nouvelle table, nouvelle colonne, nouvel
index) devrait désormais :
1. Être écrit ici, dans un nouveau fichier numéroté (`0002_...sql`),
   relisible et reviewable comme n'importe quel changement de code.
2. Être répercuté dans `SCHEMA`/`_MIGRATIONS`/`_HEAVY_MIGRATIONS` de
   `db.py` (ou l'équivalent à créer dans `user_accounts.py`) pour que
   l'application l'applique réellement.

Aucune de ces deux étapes ne touche une base de production existante
automatiquement — c'est un aide-mémoire de convention, pas un outil
d'exécution.

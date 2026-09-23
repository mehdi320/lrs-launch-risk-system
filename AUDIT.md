# Audit sécurité & qualité — LRS™

Branche dédiée : `audit/securite`, créée avant toute modification.
Mission : 20 signaux de vulnérabilité, classés OK / À CORRIGER / NON
APPLICABLE, fichier:ligne à l'appui.

Contexte technique important pour lire ce rapport : ce repo n'utilise
**pas Supabase**. Le backend est Python (FastAPI + SQLite), le frontend
public est `sales-site/` (Next.js, page de vente statique). Plusieurs des
20 points (Supabase RLS, service_role, types Supabase) sont donc NON
APPLICABLES par construction — pas une négligence, une architecture
différente de celle présupposée par la checklist.

---

## Secrets — résumé en tête (règle de la mission)

**Recherche complète effectuée sur tout l'historique git** (`git log --all
-p`, tous commits, toutes branches) : recherche de motifs `sk_live_`,
`sk_test_`, `whsec_`, `AIza...`, blocs `-----BEGIN PRIVATE KEY-----`, et
assignations `SECRET_KEY=`/`API_KEY=`/`PASSWORD=`/`TOKEN=` suivies d'une
valeur non-placeholder.

**Résultat : aucun secret réel trouvé dans l'historique.** `.env` n'a
jamais été commité (`git log --all --full-history -- .env` : vide).
Toutes les occurrences de `sk_test_`/`sk_live_`/`whsec_` dans les fichiers
trackés sont des placeholders de documentation (`.env.example`,
`PASSATION.md`, `STRIPE_SMTP_SETUP.md`) — aucune valeur réelle.

**Point de transparence (pas une fuite)** : `NEXT.md` (commit `d4c7913`,
hors de cette branche d'audit) contient une clé publique Stripe
(`pk_live_8dMJDhsBZ87pYEpgTyvk0Sw200SXHeON4h`) et un ID de bouton
(`buy_btn_1UCyXdFMKX0qC8wWSojUTEv6`), fournis par l'utilisateur en session.
Une clé `pk_live_...` est **conçue pour être publique** (elle est destinée
à être embarquée dans du code client) — ce n'est pas un secret au sens de
ce point 4, aucune révocation nécessaire. Mentionné pour que ce soit
explicite plutôt que découvert plus tard.

---

## SÉCURITÉ (critique)

### 1. RLS (Row Level Security) non activé sur les tables Supabase
**NON APPLICABLE.** Aucune trace de Supabase dans le repo (`grep -ri
supabase` sur tout le code : zéro résultat). L'isolation multi-tenant est
gérée côté application : chaque utilisateur a son propre sous-dossier de
données (`pilot_server.py:94-127`, `_current_user_ns()`), pas de RLS
PostgreSQL car pas de PostgreSQL.

### 2. Clé `service_role` exposée ou utilisée côté front
**NON APPLICABLE.** Même raison — pas de Supabase, donc pas de
`service_role`. Aucune clé de ce type trouvée dans le repo.

### 3. Secrets dans des variables préfixées `NEXT_PUBLIC_`
**OK.** Trois variables `NEXT_PUBLIC_` existent, aucune n'est un secret :
- `sales-site/.env.example:3` — `NEXT_PUBLIC_STRIPE_LINK` : un Payment
  Link Stripe, fait pour être public (c'est littéralement le lien que
  Stripe vous demande de partager).
- `sales-site/.env.example:13` — `NEXT_PUBLIC_META_PIXEL_ID` : ID de
  pixel publicitaire, public par nature (visible dans le HTML de
  n'importe quel site qui l'utilise).
- `sales-site/.env.example:18` — `NEXT_PUBLIC_GTAG_ID` : ID Google
  Analytics/Ads, même remarque.

### 4. Fichier `.env` commité (+ historique git)
**OK.** Voir résumé en tête. `.gitignore:2-4` exclut `.env`, `.env.local`,
`.env.production`. Confirmé absent de l'historique complet.

### 5. Webhook Stripe sans vérification de signature
**OK.** `creative_studio/serving/app.py:319-348` —
`stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)`
vérifie la signature. Sans `STRIPE_WEBHOOK_SECRET` configuré, l'endpoint
**refuse tout par défaut** (503, ligne 342-348) sauf opt-in explicite
`LRS_CS_ALLOW_UNVERIFIED_WEBHOOK=true` réservé au dev local (jamais actif
par défaut). Testé en conditions réelles dans une session précédente
(6/6 sur `test_stripe_webhook.py`).

### 6. CORS configuré en `*` (wildcard)
**OK.** Aucun `CORSMiddleware` ni en-tête `Access-Control-Allow-Origin`
nulle part dans le repo (`grep` sur tout le code : zéro résultat). Les
deux apps FastAPI servent leur propre frontend en same-origin
(`pilot_static/` monté directement par `pilot_server.py`) — pas de CORS
nécessaire, et surtout pas de wildcard permissif accidentel.

### 7. Authentification/token stocké dans `localStorage`
**OK.** La session (`authenticated`, `subscriber_email`) est un cookie
**HttpOnly** signé (Starlette `SessionMiddleware`, flag `httponly`
toujours actif — vérifié dans le code source de la dépendance,
`security_flags = "httponly; samesite=" + same_site`), donc inaccessible
en JavaScript. Usages de `localStorage`/`sessionStorage` trouvés dans le
repo, aucun ne concerne l'authentification :
- `pilot_static/index.html:2825,2865,3004,3011` — état UI non sensible
  (checklist de mise en ligne, tracker de recommandations).
- `sales-site/components/CookieConsent.tsx:67-82` — choix de consentement
  cookies (RGPD), par design local au navigateur.
- Les tokens d'API Ads (Meta/TikTok) saisis par l'utilisateur sont
  envoyés au serveur et stockés côté serveur (`pilot_server.py:965-976`,
  fichier par utilisateur `.lrs_ads_creds.json`), jamais en `localStorage`.

### 8. Authentification vérifiée uniquement côté client
**OK.** Gate serveur dans `pilot_server.py:154-169`
(`@app.middleware("http") async def _require_auth`) : bloque `/api/*`
avec 401 si ni `APP_PASSWORD` ni abonnement Stripe actif en session.
`_active_subscriber_email` (ligne 146-151) **revalide en base à chaque
requête** — testé en direct dans une session précédente : résiliation
d'un abonnement coupe l'accès immédiatement, même avec un cookie de
session encore valide.

### 9. Routes API sans validation de schéma
**À CORRIGER (partiel).** `pilot_server.py` utilise des modèles Pydantic
(`BaseModel`) sur la quasi-totalité de ses routes `POST`/`PUT` (20 classes
de requête définies, ex. `AuditRequest`, `FunnelAuditRequest`,
`ConsumeMagicLinkRequest`) — validation de type/présence automatique par
FastAPI, équivalent Python de Zod. Une route fait exception :
- **`creative_studio/serving/app.py:256-261`**
  (`POST /v/{test_id}/submit-form`) — endpoint **public, non authentifié**
  (formulaire d'un funnel visible par n'importe quel visiteur) qui accepte
  `await request.form()` et construit `values = {k: v for k, v in
  form_data.items() ...}` sans aucune limite : nombre de champs, longueur
  de clé, longueur de valeur, type (un visiteur pourrait envoyer un champ
  fichier là où une chaîne est attendue). Stocké tel quel dans
  `values_json` (SQLite). Corrigé en Phase 2 (voir plus bas).

---

## PERFORMANCE ET BASE DE DONNÉES

### 10. `select *` sans pagination
**À CORRIGER (risque actuel faible).** `SELECT *` sans `LIMIT` dans
`user_accounts.py:137` et 17 occurrences dans
`creative_studio/storage/repository.py` (lignes 65, 71, 105, 111, 163,
174, 310, 368, 375, 386, 397, 438, 471, 532, 568, 626). Toutes filtrées
par clé étrangère (`product_id`, `test_id`, `step_id`...), donc bornées
par construction tant que le volume par tenant reste faible (bêta,
quelques dizaines d'utilisateurs par `PASSATION.md`) — pas un risque
actif aujourd'hui, mais aucune limite explicite si un compte accumule
beaucoup de données. Non corrigé (Phase 3, liste seulement).

### 11. Pas d'index sur les colonnes filtrées ou jointes
**À CORRIGER.** Colonnes filtrées dans des `WHERE` sans index dédié :
- `products.tenant_id` — filtré `creative_studio/storage/repository.py:71`,
  pas d'index (seule la `PRIMARY KEY(id)` existe,
  `creative_studio/storage/db.py:23-33`).
- `variants.product_id` — filtré `repository.py:111`, pas d'index
  (`db.py:35-47`).
- `ab_tests.product_id` — filtré `repository.py:174`, pas d'index
  (`db.py:49-59`).
- `funnels.product_id` — filtré `repository.py:368`, pas d'index
  (`db.py:105-115`).
- `email_sequences.product_id` — filtré `repository.py:626`, pas d'index
  (`db.py:184-192`).
- `magic_links.email` — filtré `user_accounts.py:207-212` (anti-spam lien
  magique), pas d'index (`user_accounts.py:69-74`, seule la `PRIMARY
  KEY(token)` existe).

D'autres tables ont déjà des index adaptés (`events`, `funnel_steps`,
`funnel_step_media`, `funnel_step_elements`, `form_submissions`,
`users.stripe_subscription_id`) — le pattern existe dans le repo, juste
pas appliqué partout. Non corrigé (Phase 3, liste seulement — ajouter un
index touche le schéma, hors du périmètre "sans casser l'existant" pour
une correction automatique non supervisée).

### 12. Requêtes N+1 dans les boucles
**À CORRIGER.** Pas de N+1 côté base de données (aucun trouvé). En
revanche, N+1 classique sur une **API externe** :
- `ads_api.py:32` (`fetch_meta_campaigns`) — boucle sur les campagnes
  (jusqu'à 10, `campaigns_raw[:10]`) avec **une requête HTTP séparée par
  campagne** vers `graph.facebook.com/.../insights` (ligne 44).
- `ads_api.py:109` (`fetch_tiktok_campaigns`) — même pattern pour TikTok.

Impact : jusqu'à 10 requêtes séquentielles (≈15s de timeout chacune) pour
un seul clic "Importer mes campagnes". Non corrigé (Phase 3).

### 13. Aucune migration, schéma modifié directement sur main
**À CORRIGER (partiel).** Nuance importante : `creative_studio/storage/
db.py` a un **vrai système de migrations versionnées** — `_MIGRATIONS`
(ALTER TABLE idempotents, lignes 208-215) + `_HEAVY_MIGRATIONS` (rebuilds
de table suivis par une table `schema_migrations`, lignes 296-331).
Fonctionnel, mais embarqué en chaînes Python plutôt qu'en fichiers `.sql`
relisibles indépendamment de l'app. `user_accounts.py:56-84` n'a
**aucun** mécanisme de migration — juste `CREATE TABLE IF NOT EXISTS`
exécuté au démarrage (`init_db()`, ligne 98-104) ; toute évolution de
schéma future y serait ad hoc. **Corrigé en Phase 2** — génération de
fichiers de migration SQL relisibles (baseline), sans toucher à la
production.

---

## QUALITÉ DU CODE

### 14. Usage de `any` et types Supabase non régénérés
**OK / NON APPLICABLE.** Aucun `any` dans le code TypeScript écrit à la
main (`sales-site/app/*.tsx`, `sales-site/components/*.tsx`) — les seules
occurrences sont dans `.next/types/` (généré automatiquement par le build
Next.js, jamais commité — voir `.gitignore`) et dans `node_modules`. Pas
de Supabase donc pas de types à régénérer.

### 15. `"use client"` sur des composants qui n'en ont pas besoin
**OK.** Un seul fichier utilise `"use client"` dans tout `sales-site/` :
`sales-site/components/CookieConsent.tsx`. Légitime — le composant utilise
`useState`/`useEffect`/`localStorage`, des API strictement côté client.

### 16. Fichiers `page.tsx` démesurés (ex. 800 lignes)
**OK**, sous le seuil donné, mais volumineux — à surveiller :
- `sales-site/app/vente/page.tsx` — 497 lignes.
- `sales-site/app/vente/fr/page.tsx` — 511 lignes.

Les deux pages dupliquent une structure quasi identique (EN/FR) ; pas de
composant partagé pour le contenu (seulement pour l'UI,
`vente-shared.tsx`). Recommandation en Phase 3.

### 17. `catch (e) { console.log(e) }` sans vraie gestion d'erreur
**À CORRIGER (partiel).** Aucune occurrence dans le code TypeScript écrit
à la main (zéro `catch`/`console.log` hors `node_modules`). Côté Python :
**25 blocs `except Exception:` génériques** répartis sur 11 fichiers
(liste complète : `user_accounts.py:114`, `jsonstore.py:14,23`,
`email_alerts.py:185,276,325`, `creative_studio/storage/db.py:356`,
`creative_studio/serving/app.py:373`, `creative_studio/core/
llm_client.py:35`, `creative_studio/core/pdf_export.py:189,244,264`,
`creative_studio/core/reference_extraction.py:157`,
`audit_engine.py:156,249,947`, `pilot_server.py:35,115,414,1187,1425,
1521,1558,1575`, `integrations.py:75`). La majorité suit un pattern de
dégradation contrôlée voulu (`return False`/`None`/`pass` avec commentaire
expliquant pourquoi — ex. `jsonstore.py:23` "silencieux si pas de droits
d'écriture") plutôt qu'un vrai anti-pattern "attrape et ignore
aveuglément". Le vrai problème : **aucun de ces blocs ne journalise
l'exception** — un échec silencieux ne laisse aucune trace exploitable en
prod. Non corrigé (Phase 3).

### 18. Abonnements realtime sans `unsubscribe` au démontage
**NON APPLICABLE.** Aucun `WebSocket`, `EventSource`, `.subscribe(` ni
mécanisme realtime nulle part dans le repo (recherche complète,
`*.py`/`*.ts`/`*.tsx`/`*.html`, zéro résultat). Tout le frontend
(`pilot_static/index.html`) utilise du `fetch()` classique, pas
d'abonnement à démonter.

### 19. TODO laissés par l'IA
**OK.** Aucun `TODO`/`FIXME`/`XXX` dans le code écrit à la main. La seule
occurrence trouvée (`sales-site/app/layout.tsx:19`) est un commentaire
expliquant un format d'exemple ("G-XXXXXXX" — un ID Google Analytics
factice), pas un marqueur de tâche.

---

## COÛT ET ABUS

### 20. Aucun rate limit sur les appels LLM
**À CORRIGER.** Cinq endpoints déclenchent des appels OpenAI/Anthropic
sans aucune limite par utilisateur : `pilot_server.py:337`
(`POST /api/audit`), `pilot_server.py:287` (`POST /api/funnel-audit`),
`pilot_server.py:573` (`POST /api/bulk-audit`, jusqu'à 20 audits en un
seul appel), `pilot_server.py:634` (`POST /api/creative-angles`),
`pilot_server.py:1214` (`POST /api/creative-studio/generate`). Le seul
rate limit existant dans le repo protège le **login**
(`pilot_server.py:1270-1293`, `_login_rate_limited`), rien d'équivalent
pour les endpoits qui coûtent réellement de l'argent (appels API
facturés à l'usage). Un compte abonné (ou quelqu'un avec le mot de passe
admin) peut aujourd'hui générer un nombre illimité de requêtes LLM.
**Corrigé en Phase 2.**

---

## Phase 2 — Correctifs appliqués

_Complétée après la rédaction de ce rapport — voir section dédiée plus
bas et les commits de la branche `audit/securite`._

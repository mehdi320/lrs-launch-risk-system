# NEXT — État réel et plan (audit du 2026-09-20, mis à jour le 2026-09-23)

**Mise à jour du 2026-09-23** — beaucoup de mouvement depuis le 20 :
- Audit sécurité/qualité complet sur branche `audit/securite`, mergé dans
  `main` (voir `AUDIT.md` à la racine pour le détail des 20 points).
- **Pendant ce même audit, une session indépendante a fait un pentest actif
  directement sur `main`** (7 commits : quota LLM par utilisateur, CSRF,
  fail-closed en prod, échappement HTML des emails, headers CSP stricts,
  chiffrement des tokens Ads Meta/TikTok au repos, protection SSRF
  renforcée avec anti DNS-rebinding). Réconcilié sans perte — voir le
  commit de merge sur `main`.
- **OpenAI entièrement retiré** — Claude (Anthropic) est désormais l'unique
  moteur LLM de LRS, audit ET Creative Studio. Sans `ANTHROPIC_API_KEY`,
  erreur claire plutôt qu'un fallback silencieux vers OpenAI.
- **Centre de notifications in-app ajouté** — chute de score et digest de
  monitoring créent une notification dans l'app (cloche en haut à droite)
  au lieu de ne partir QUE par email comme avant. L'email est désormais une
  case à cocher optionnelle (préférence globale par utilisateur), plus un
  champ par planification.

Le reste de ce document (ci-dessous) date du 20 septembre — toujours valide
pour la partie "attend la paye" (domaine, VPS, Stripe Live), mais certaines
mentions de `PASSATION.md` "en retard" sont maintenant partiellement
résolues (voir ses propres mises à jour).

---

## 1. Ce qui est fait

- Architecture d'accès tranchée et codée : le pilote FastAPI est l'unique
  interface, gate par `APP_PASSWORD` (admin) OU abonnement Stripe actif
  revérifié à chaque requête (`pilot_server.py:154-169`, commit `97c28bc`).
- `app.py`/Streamlit entièrement retiré du code et du déploiement
  (commits `2a6f42e`, `392c90d`, `97c28bc`).
- Paiement → webhook → lien magique → email : logique complète et durcie
  (dédup d'event Stripe, race condition sur la consommation du lien
  magique corrigée, anti-spam, anti-injection d'en-tête email) —
  `creative_studio/serving/app.py`, `user_accounts.py`, commits `3b95983`,
  `d6721a1`, `a9e9bda`.
- Socle sécurité : SSRF sur les URLs auditées, brute-force login,
  isolation multi-tenant par utilisateur, XSS sur sortie LLM (commits
  `a9e9bda`, `00c9160`, `22fbbe8`, `9c6eecf`).
- `docker-compose.yml` (3 services : pilot, serving, caddy) + `Caddyfile`
  (TLS Let's Encrypt auto) prêts côté code — **jamais testés sur un
  démon Docker réel** (`DEPLOYMENT.md:3-4`).
- Revue de sécurité complète du repo faite le 2026-09-21 (au-delà du diff
  habituel) : un point réel trouvé et corrigé — SSRF via redirection HTTP
  non revalidée dans `creative_studio/core/pdf_export.py::_image_bytes`
  (commit `8427dac`), non exploitable via l'app déployée actuellement
  (chemin d'appel orphelin depuis le retrait de Streamlit) mais corrigé
  quand même avant que le code ne soit reconnecté. Reste de l'audit
  (`user_accounts.py`, `email_alerts.py`, `integrations.py`, webhook
  Stripe, XSS du rendu Funnel 2 étapes) : rien trouvé.

## 2. Ce qui dépend de votre machine — à vérifier sur place

Je n'ai trouvé aucun fichier `.env` dans le repo (seul `.env.example`
existe). Impossible de confirmer depuis le code :
- Si le produit/prix Stripe **Test** existe réellement dans votre dashboard
  et si `STRIPE_BETA_PRICE_ID` est renseigné.
- Si `SMTP_HOST/USER/PASSWORD` pointent vers un compte SMTP réel qui
  fonctionne (`python3 test_smtp.py` à lancer chez vous, cf.
  `STRIPE_SMTP_SETUP.md:168-175`).
- La valeur réelle d'`APP_PASSWORD`. Note : le risque "change-moi" signalé
  dans `PASSATION.md:322-324` concernait `.streamlit/secrets.toml`, qui
  **n'existe plus** (Streamlit supprimé). Le code actuel
  (`pilot_server.py:39-40`) lit `APP_PASSWORD` sans défaut faible — reste
  à vérifier que votre `.env` local en contient bien une valeur forte.
- Docker Desktop/containers lancés, `docker build`/`docker compose up`
  validés — aucun démon Docker disponible dans cet environnement d'audit.

## 3. Tâches restantes, par priorité

Séparées en deux blocs : ce qui est **gratuit** (mode Stripe Test, aucun
achat) et ce qui **attend la paye** (domaine, VPS, Stripe Live — argent
réel). Pas de raison de bloquer le premier bloc sur le second.

### Gratuit — faisable dès maintenant

| # | Tâche | Qui | Temps estimé |
|---|---|---|---|
| 1 | ~~Bug `LRS_APP_URL`~~ — **fait** (commit `ef8fae2`) | Claude Code seul | fait |
| 2 | ~~`.env` de test créé + serveurs lancés~~ — **fait le 2026-09-21** dans cette session cloud (`APP_PASSWORD`, `APP_SECRET_KEY`, `LRS_APP_URL`, `LRS_SALES_PAGE_URL` remplis ; `STRIPE_SECRET_KEY`/`STRIPE_BETA_PRICE_ID`/`SMTP_*` laissés vides, je n'ai pas vos identifiants réels). **Reste à vous** : reprendre ce `.env` avec vos vraies valeurs Stripe Test + SMTP (voir §2 ci-dessus pour le détail) — le fichier n'existe que dans cette session éphémère, pas sur votre machine. | Claude Code (squelette fait) + Baki (vraies valeurs Stripe/SMTP) | 15 min pour vous |
| 3 | ~~Tester le parcours~~ — **partiellement fait le 2026-09-21**, sans navigateur ni vraie carte : suite `test_stripe_webhook.py` 6/6, login admin (bon/mauvais mot de passe), lien magique consommé une fois puis bloqué en réutilisation, **et résiliation testée : l'accès est coupé immédiatement même avec un cookie de session valide** — confirme que le gate se revérifie à chaque requête, pas seulement au login. Non testé (nécessite vos identifiants réels) : un vrai paiement via la page Stripe Checkout dans un navigateur, un vrai email reçu par SMTP. | Claude Code (logique validée) + Baki (test réel carte + email) | 15-20 min pour vous |
| 4 | ~~Supprimer `webhook_server.py`~~ — **fait** (commit `ef8fae2`) | Claude Code seul | fait |
| 5 | ~~Corriger le défaut `LRS_APP_URL`~~ — **fait** (commit `ef8fae2`) | Claude Code seul | fait |
| 6 | ~~Réécrire `PASSATION.md`~~ — **fait**, brouillon poussé (commit `ef8fae2`) ; reste la validation du contenu produit par Baki | Claude Code (fait) + Baki (validation) | à valider |
| 11 | ~~Corriger le Root Directory du projet Vercel~~ — **fait le 2026-09-21**, par Baki directement dans le dashboard (l'appel API depuis cette session cloud était bloqué par la politique réseau, jamais résolu par le token). Root Directory = `sales-site`, Framework Preset repassé sur Next.js (était resté sur la détection Python héritée de l'ancienne racine du repo). Build **Ready**, `/vente` vérifié en ligne. | Baki | fait |

### Chemin rapide — ouvrir les ventes sans VPS (ngrok) — écarté pour l'instant

Correction du 2026-09-21 : le VPS n'est **pas** un prérequis technique pour
que le bouton d'abonnement fonctionne en vrai. Il ne sert qu'à une chose —
recevoir le webhook Stripe qui active le compte. Un tunnel `ngrok` fait ça
gratuitement, tout de suite, tant que le PC de Baki reste allumé et le
process actif (fragile, pas du "vrai" hébergement).

**Décision de Baki (2026-09-21, même session) : on n'utilise pas ce
raccourci.** Tout — webhook Live inclus — attend la paye et le VPS durable
(section suivante). Les tâches 13-18 restent documentées ci-dessous à
titre de référence si la décision change, mais ne sont **pas** le plan
actuel.

| # | Tâche | Qui | Temps estimé |
|---|---|---|---|
| 13 | Installer `ngrok`, lancer `ngrok http 8000` pour obtenir une URL HTTPS publique vers le service webhook local | Baki | 10 min |
| 14 | Remplir un vrai `.env` (sur la machine de Baki, pas dans cette session éphémère) avec les vraies valeurs **Live** : `STRIPE_SECRET_KEY` (`sk_live_...`), `STRIPE_BETA_PRICE_ID` (celui déjà actif, trouvé sur le dashboard Live), `SMTP_*` réels | Baki | 10 min |
| 15 | Créer l'endpoint webhook dans Stripe Dashboard (mode **Live**) pointant vers l'URL ngrok + `/webhook/stripe`, écoutant `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted` ; copier le `whsec_...` dans `.env` (`STRIPE_WEBHOOK_SECRET`) | Baki | 5 min |
| 16 | Lancer `uvicorn creative_studio.serving.app:app --port 8000` (avec ce vrai `.env`, sans `LRS_CS_ALLOW_UNVERIFIED_WEBHOOK`) | Baki | 2 min |
| 17 | Brancher le bouton sur `sales-site/` — soit `NEXT_PUBLIC_STRIPE_LINK` (Payment Link) dans Vercel → Environment Variables, soit intégrer le snippet Stripe Buy Button déjà fourni (`buy_btn_1UCyXdFMKX0qC8wWSojUTEv6` / `pk_live_8dMJDhsBZ87pYEpgTyvk0Sw200SXHeON4h`) dans `sales-site/components/vente-shared.tsx` à la place de `<a href={STRIPE_LINK}>`. Redéployer. | Claude Code (le snippet) ou Baki (l'env var Vercel) | 15 min |
| 18 | Test réel : un paiement (le vôtre ou celui d'un vrai client), vérifier que l'email avec le lien magique arrive et que l'accès au pilote se débloque | Baki | 5-10 min |

### Durable — VPS + domaine (argent réel, à faire quand la paye tombe)

Seul chemin retenu pour ouvrir les ventes en Live (Baki a écarté le
raccourci ngrok ci-dessus) — donc redevient le vrai bloquant avant tout
paiement réel, en attendant la paye.

| # | Tâche | Qui | Temps estimé |
|---|---|---|---|
| 7 | Provisionner le VPS (GCP `e2-micro` free tier — gratuit, mais acheter le nom de domaine ne l'est pas) + pointer les 3 A records (`app.`, `pilot.`, `api.`) — jamais fait (`PASSATION.md` §5.2, `DEPLOYMENT.md` checklist) | Baki | 1-2h |
| 8 | `docker compose up -d` sur le serveur réel, vérifier que Caddy obtient les certificats TLS (`docker compose logs caddy`), reconfigurer l'endpoint webhook Stripe avec la vraie URL publique (remplace l'URL ngrok de la tâche 15) | Baki — **à vérifier sur place**, dépend d'un serveur/Docker réels, bloqué sur 7 | 30-60 min |
| 9 | Configurer l'endpoint webhook Stripe (mode **Live**) sur l'URL VPS stable, écoutant `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted` — copier le `whsec_...` dans le `.env` du VPS | Baki | 10 min |
| 10 | Faire relire `privacy.html`/`terms.html` (pilote) et créer l'équivalent pour `sales-site/` par un professionnel — toujours vrai, aucun commit de revue légale trouvé après `85a7b90`. Coûte probablement aussi de l'argent (juriste). | Baki (externe) | hors périmètre technique |
| 12 | Brancher le bouton Stripe Live sur `sales-site/` — soit `NEXT_PUBLIC_STRIPE_LINK` (Payment Link) dans Vercel → Environment Variables, soit intégrer le snippet Stripe Buy Button déjà fourni (`buy_btn_1UCyXdFMKX0qC8wWSojUTEv6` / `pk_live_8dMJDhsBZ87pYEpgTyvk0Sw200SXHeON4h`) dans `sales-site/components/vente-shared.tsx` à la place de `<a href={STRIPE_LINK}>`. Redéployer. | Claude Code (le snippet) ou Baki (l'env var Vercel) | 15 min |

## 4. Plan lundi/mardi

**Lundi matin (Baki)** — Créer le produit/prix Stripe Test si absent,
copier `.env.example` en `.env` sur votre machine et remplir
`STRIPE_SECRET_KEY`/`STRIPE_BETA_PRICE_ID`/`STRIPE_WEBHOOK_SECRET`/
`SMTP_*` (le reste des valeurs est déjà vérifié correct — tâche 2,
~15 min).

**Lundi après-midi (Baki)** — Lancer `uvicorn pilot_server:app --port
8600`, `uvicorn creative_studio.serving.app:app --port 8000`, `stripe
listen`, dérouler le parcours complet de paiement test avec une vraie
carte et un vrai email (tâche 3 — la logique webhook/lien magique/gate
est déjà validée, il reste juste à confirmer le chemin navigateur+email).
Relire le brouillon de `PASSATION.md` (tâche 6). Le fix Vercel (tâche 11)
est déjà fait.

**À la paye (Baki)** — Acheter le domaine, provisionner le VPS GCP + DNS
(tâche 7, ~1-2h), puis `docker compose up -d` sur le serveur réel,
vérification TLS Caddy, brancher le webhook Stripe Live sur l'URL publique
(tâches 8-9). Revue légale (tâche 10) et branchement du bouton Live
(tâche 12) suivent une fois l'infra publique stable. C'est le seul plan
retenu — le chemin ngrok (tâches 13-18) a été explicitement écarté par
Baki le 2026-09-21, ne pas le proposer à nouveau sans qu'il le redemande.

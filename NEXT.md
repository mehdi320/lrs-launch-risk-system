# NEXT — État réel et plan (audit du 2026-09-20)

Audit en lecture seule sur `claude/lrs-audit-post-merge-a31f47` (= `main`,
HEAD `f94c2df`, aucun commit d'écart dans un sens ou l'autre). Chaque
affirmation ci-dessous pointe vers un fichier ou un commit — aucune
supposition sur l'état de votre machine (Docker, `.env` réel).

**Correction importante** : `PASSATION.md` date du 7 septembre (commit
`a77fc89`) et se trouve **22 commits en retard** sur HEAD. Il décrit encore
`app.py`/Streamlit comme existant et l'architecture d'accès du pilote comme
"non tranchée" — les deux sont faux aujourd'hui (voir ci-dessous). Ne pas
réamorcer une session sur ce document sans le recouper.

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

### Attend la paye — domaine, VPS, Stripe Live (argent réel)

| # | Tâche | Qui | Temps estimé |
|---|---|---|---|
| 7 | Provisionner le VPS (GCP `e2-micro` free tier — gratuit, mais acheter le nom de domaine ne l'est pas) + pointer les 3 A records (`app.`, `pilot.`, `api.`) — jamais fait (`PASSATION.md` §5.2, `DEPLOYMENT.md` checklist) | Baki | 1-2h |
| 8 | `docker compose up -d` sur le serveur réel, vérifier que Caddy obtient les certificats TLS (`docker compose logs caddy`), reconfigurer l'endpoint webhook Stripe avec la vraie URL publique | Baki — **à vérifier sur place**, dépend d'un serveur/Docker réels, bloqué sur 7 | 30-60 min |
| 9 | Passer Stripe en Live (ré-autoriser le CLI, créer produit/prix Live, `sk_live_...`, webhook Dashboard réel) — bloqué tant que 7-8 ne sont pas faits (Stripe doit joindre l'endpoint publiquement) | Baki | 30 min une fois l'infra prête |
| 10 | Faire relire `privacy.html`/`terms.html` (pilote) et créer l'équivalent pour `sales-site/` par un professionnel — toujours vrai, aucun commit de revue légale trouvé après `85a7b90`. Coûte probablement aussi de l'argent (juriste). | Baki (externe) | hors périmètre technique |
| 12 | Brancher le bouton Stripe Live sur `sales-site/` — **décidé le 2026-09-21 : on attend le VPS**, pas de branchement avant, pour ne pas faire payer un client réel sans que le webhook d'activation existe (pas de backend public = paiement pris, personne n'active le compte). Snippet Stripe Buy Button déjà fourni par Baki, à utiliser tel quel une fois 7-8 faits : `<script async src="https://js.stripe.com/v3/buy-button.js"></script>` + `<stripe-buy-button buy-button-id="buy_btn_1UCyXdFMKX0qC8wWSojUTEv6" publishable-key="pk_live_8dMJDhsBZ87pYEpgTyvk0Sw200SXHeON4h"></stripe-buy-button>` (clé publique, pas de risque à la garder en clair). À intégrer dans `sales-site/components/vente-shared.tsx` à la place du `<a href={STRIPE_LINK}>` actuel, ou en gardant les deux en parallèle. | Claude Code, une fois 7-9 faits | 15 min |

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

**Mardi (Baki, une fois la paye tombée)** — Acheter le domaine,
provisionner le VPS GCP + DNS (tâche 7, ~1-2h), puis `docker compose up
-d` sur le serveur réel, vérification TLS Caddy, bascule webhook Stripe
vers l'URL publique (tâche 8). Stripe Live (tâche 9) et revue légale
(tâche 10) suivent une fois l'infra publique stable — pas forcément le
même jour si la paye/l'achat du domaine prend plus de temps que prévu.

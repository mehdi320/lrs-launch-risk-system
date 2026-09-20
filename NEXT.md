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

| # | Tâche | Qui | Temps estimé |
|---|---|---|---|
| 1 | **Bug réel** : `LRS_APP_URL` a pour défaut `http://localhost:8501` (ancien port Streamlit, supprimé) dans `creative_studio/serving/app.py:71`, `webhook_server.py:25` et `.env.example:65`. Sans valeur explicite dans `.env` pointant vers le pilote (port 8600, ou `https://app.<domaine>` derrière Caddy), le lien magique envoyé par email pointe vers une adresse morte. | Baki (remplir `.env`) | 5 min |
| 2 | Remplir `.env` complet : `STRIPE_SECRET_KEY`, `STRIPE_BETA_PRICE_ID` (créer le produit/prix Stripe mode Test si pas fait — `STRIPE_SMTP_SETUP.md` §1), `STRIPE_WEBHOOK_SECRET`, `SMTP_*`, `APP_PASSWORD` réel, `LRS_APP_URL` correct (point 1) | Baki | 20 min |
| 3 | Tester le parcours complet en local (paiement test carte `4242...` → webhook → email reçu → lien magique → accès pilote débloqué), maintenant que le gate est réellement branché sur le pilote — suivre `STRIPE_SMTP_SETUP.md` §3 | Baki | 30-45 min |
| 4 | Supprimer `webhook_server.py` — code mort : référence `app.py`/Streamlit et le port 8501, n'est appelé par aucun service dans `docker-compose.yml` ni `Dockerfile` (seul `creative_studio/serving/app.py` est réellement utilisé). Risque de confusion pour une future session. | Claude Code seul | 10 min |
| 5 | Corriger le défaut `LRS_APP_URL=http://localhost:8501` dans `.env.example` (→ `http://localhost:8600`) et la mention "URL publique de l'app Streamlit" dans `STRIPE_SMTP_SETUP.md:186` (→ pilote) | Claude Code seul | 10 min |
| 6 | Réécrire `PASSATION.md` pour refléter l'état réel (app.py supprimé, gate résolu, 22 commits d'historique manquants) — évite de réamorcer une session sur de fausses prémisses | Claude Code (rédaction) + Baki (validation du contenu produit) | 30-45 min |
| 7 | Provisionner le VPS (GCP `e2-micro` free tier) + acheter le nom de domaine + pointer les 3 A records (`app.`, `pilot.`, `api.`) — jamais fait (`PASSATION.md` §5.2, `DEPLOYMENT.md` checklist) | Baki | 1-2h |
| 8 | `docker compose up -d` sur le serveur réel, vérifier que Caddy obtient les certificats TLS (`docker compose logs caddy`), reconfigurer l'endpoint webhook Stripe avec la vraie URL publique | Baki — **à vérifier sur place**, dépend d'un serveur/Docker réels | 30-60 min |
| 9 | Passer Stripe en Live (ré-autoriser le CLI, créer produit/prix Live, `sk_live_...`, webhook Dashboard réel) — bloqué tant que 7-8 ne sont pas faits (Stripe doit joindre l'endpoint publiquement) | Baki | 30 min une fois l'infra prête |
| 10 | Faire relire `privacy.html`/`terms.html` (pilote) et créer l'équivalent pour `sales-site/` par un professionnel — toujours vrai, aucun commit de revue légale trouvé après `85a7b90` | Baki (externe) | hors périmètre technique |
| 11 | Redéployer `sales-site/` sur Vercel **en preview d'abord** (dernier commit sales-site : `1addf3e`, avant l'incident de déploiement prod accidentel décrit dans `PASSATION.md` §2) | Baki | 20 min |

## 4. Plan lundi/mardi

**Lundi matin (Baki)** — Créer le produit/prix Stripe Test si absent,
remplir `.env` complet (tâches 1-2 ci-dessus, ~30 min).

**Lundi après-midi (Baki, en parallèle Claude Code)** — Baki : lancer
`uvicorn pilot_server:app --port 8600`, `uvicorn
creative_studio.serving.app:app --port 8000`, `stripe listen`, dérouler le
parcours complet de paiement test (tâche 3). Pendant ce temps, Claude Code
peut faire seul : supprimer `webhook_server.py` (tâche 4), corriger les
défauts `LRS_APP_URL` dans la doc (tâche 5), réécrire `PASSATION.md`
(tâche 6, brouillon — validation ensuite par Baki).

**Mardi matin (Baki)** — Provisionner le VPS GCP + domaine + DNS (tâche
7, ~1-2h — aucune partie de ceci ne peut être faite par Claude Code, accès
compte cloud/registrar requis).

**Mardi après-midi (Baki)** — `docker compose up -d` sur le serveur réel,
vérification TLS Caddy, bascule webhook Stripe vers l'URL publique (tâche
8, "à vérifier sur place"). Si le temps le permet : redéployer
`sales-site/` en preview Vercel (tâche 11). Stripe Live (tâche 9) et revue
légale (tâche 10) restent pour une session suivante, une fois l'infra
publique stable.

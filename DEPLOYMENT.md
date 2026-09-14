# Déploiement — squelette

Statut : **squelette non testé en conditions réelles**. Écrit sans démon
Docker disponible ni clés Meta/Claude configurées — à valider avant tout
déploiement réel (voir checklist en bas).

## Fichiers

- `Dockerfile` — image unique pour les trois surfaces web (pilote FastAPI
  `pilot_server.py` sur le port 8600, app Streamlit `app.py` sur le port
  8501, service de diffusion/webhook Stripe
  `creative_studio.serving.app` sur le port 8000), qui partagent le même
  code et les mêmes dépendances (`requirements.txt`). Le service lancé
  dépend de la commande (CMD par défaut : le pilote).
- `docker-compose.yml` — orchestration locale/VPS des trois services à
  partir de la même image, plus un service `caddy` qui termine le TLS
  public (voir section TLS ci-dessous). Pensé pour un VPS simple (bind
  mount, voir limitation de persistance ci-dessous) — pas pour un PaaS à
  filesystem éphémère (Fly.io, Render...).
- `Caddyfile` — configuration du reverse proxy : route
  `app.<LRS_DOMAIN>` → Streamlit, `pilot.<LRS_DOMAIN>` → pilote FastAPI,
  `api.<LRS_DOMAIN>` → service de diffusion/webhook Stripe. Certificats
  Let's Encrypt obtenus et renouvelés automatiquement par Caddy.
- `.dockerignore` — exclut secrets locaux (`.env`), état runtime
  (`.lrs_*.json`, `.lrs_*.db`) et caches de l'image.

## TLS / reverse proxy

Les 3 services applicatifs ne terminent pas le TLS eux-mêmes (voir
checklist) — c'est le rôle du service `caddy` dans `docker-compose.yml`.
Étapes pour l'activer :

1. Pointer 3 enregistrements DNS de type A vers l'IP du serveur :
   `app.<domaine>`, `pilot.<domaine>`, `api.<domaine>`.
2. Définir `LRS_DOMAIN=<domaine>` dans `.env` (sans le sous-domaine, ex.
   `LRS_DOMAIN=lrs-app.com`).
3. Ouvrir les ports 80 et 443 sur le serveur (nécessaires pour la
   validation Let's Encrypt ET le trafic HTTPS ensuite).
4. `docker compose up -d` — Caddy obtient les certificats au premier
   démarrage (peut prendre jusqu'à une minute, voir `docker compose logs
   caddy` en cas de souci).
5. `LRS_APP_URL=https://app.<domaine>` et l'URL du webhook Stripe
   (Dashboard) = `https://api.<domaine>/webhook/stripe`.

Les ports 8501/8600/8000 restent liés à `127.0.0.1` sur l'hôte (debug via
tunnel SSH uniquement, jamais exposés directement).

## Persistance des données — limitation connue

`app.py` et `pilot_server.py` écrivent leur état (historique, projets,
planification, etc. — voir `PILOT_UI.md`) dans des fichiers `.lrs_*.json`
situés **à côté du code**, pas dans un répertoire de données dédié. Le
Creative Studio ajoute `.lrs_creative_studio.db` (SQLite, funnels/tests
A/B) et `user_accounts.py` ajoute `.lrs_users.db` (SQLite, comptes/statut
d'abonnement Stripe — volontairement séparé de `.lrs_creative_studio.db`,
voir sa docstring) au même endroit.

`docker-compose.yml` contourne ça pour l'instant avec un bind mount
`.:/app` (le dépôt hôte remplace le code copié dans l'image) : l'état
persiste directement dans le dépôt, comme en local sans Docker. Ça marche
pour un VPS simple, mais **pas** pour une plateforme à filesystem éphémère
(Fly.io, Render, la plupart des PaaS) où le disque du conteneur ne
survit pas aux redéploiements.

Avant un vrai déploiement sur une telle plateforme, il faudra :
1. Ajouter un `LRS_DATA_DIR` (env var, défaut = répertoire actuel pour ne
   rien casser en local) et faire pointer chaque `*_FILE = os.path.join(...)`
   dessus dans `app.py`, `pilot_server.py`, `jsonstore.py` et
   `creative_studio/storage/db.py`.
2. Monter un volume persistant de la plateforme sur ce répertoire.

Non fait ici : changement transverse (10+ fichiers d'état, deux modules
Streamlit/FastAPI) trop risqué pour un squelette non testé — à traiter une
fois la plateforme cible choisie.

## Checklist avant déploiement réel

- [ ] Choisir une plateforme (VPS Docker, Fly.io, Render, Streamlit Cloud
      pour `app.py` seul...) — conditionne si la limitation ci-dessus doit
      être résolue d'abord.
- [ ] `docker build .` et `docker compose up` validés localement (non fait
      ici, pas de démon Docker disponible pendant l'écriture de ce
      squelette).
- [ ] Clés API en place : `OPENAI_API_KEY` et/ou `ANTHROPIC_API_KEY`
      (l'audit du pilote préfère Claude dès qu'`ANTHROPIC_API_KEY` est
      configurée — voir `audit_engine.py::run_audit()` — sinon retombe sur
      OpenAI).
- [ ] `APP_PASSWORD` + `APP_SECRET_KEY` définis si le pilote doit être
      protégé par mot de passe (sinon accès libre sur `/api/*` — voir
      `PILOT_UI.md` ; le pilote affiche un avertissement au démarrage
      (stderr) tant qu'`APP_PASSWORD` n'est pas défini, à surveiller sur les
      logs de la plateforme). `/api/auth/login` est protégé contre le
      brute-force (5 essais / 60s puis verrou de 60s, par IP cliente).
- [ ] `APP_HTTPS_ONLY=true` dès que le pilote tourne derrière un reverse
      proxy qui termine le TLS — sinon le cookie de session n'a pas le flag
      `Secure` et peut fuiter sur une requête HTTP en clair accidentelle.
      Laissé à `false` par défaut pour ne pas casser le dev local (uvicorn
      seul, sans TLS).
- [ ] Clés Meta/TikTok Ads si la Connexion API Pub doit fonctionner en
      prod (`ads_api.py`).
- [ ] SMTP (`SMTP_HOST/PORT/USER/PASSWORD`) — nécessaire pour les emails
      (rapport d'audit, alertes monitoring, digest, `email_alerts.py`) et
      **obligatoire** pour le lien magique de connexion à l'app (voir
      `user_accounts.py`) : sans SMTP configuré, un utilisateur activé par
      Stripe ne peut pas recevoir son lien d'accès.
- [ ] `STRIPE_WEBHOOK_SECRET` — obligatoire dès que le service de diffusion
      (`creative_studio.serving.app`, port 8000) doit vérifier des
      événements réels. Sert désormais à deux choses sur le même endpoint
      `/webhook/stripe` : confirmation d'achat funnel Creative Studio, et
      activation/mise à jour de l'abonnement LRS (voir
      `check_subscription_access()` dans `app.py`). Dans le Dashboard
      Stripe, l'endpoint doit écouter `checkout.session.completed`,
      `customer.subscription.updated` et `customer.subscription.deleted`.
- [ ] `STRIPE_BETA_PRICE_ID`, `LRS_APP_URL`, `LRS_SALES_PAGE_URL` —
      nécessaires pour que `/checkout/beta` (Session Checkout du plan
      bêta) et le lien magique envoyé par email fonctionnent. Sans
      `LRS_SALES_PAGE_URL`, `/checkout/beta` refuse de créer une session
      (pas de `cancel_url` fiable).
      → Voir **`STRIPE_SMTP_SETUP.md`** pour le guide pas-à-pas complet
      (créer le produit/prix, configurer le webhook, tester avec
      `test_smtp.py` et `test_stripe_webhook.py` avant la mise en prod).
- [ ] Healthcheck : `GET /api/health` (pilote) répond `{"status":"ok"}`
      sans authentification, même si `APP_PASSWORD` est défini — à
      brancher sur le mécanisme de la plateforme (Docker `HEALTHCHECK`,
      load balancer...).
- [x] Reverse proxy / TLS — géré par le service `caddy` (voir section TLS
      ci-dessus). Reste à faire : pointer le DNS et définir `LRS_DOMAIN`.
- [ ] Sauvegarde du volume de données une fois la persistance résolue
      (historique d'audits, base Creative Studio, base comptes/abonnements
      `.lrs_users.db`).

## Hors périmètre de ce squelette

- `mcp_server/` — serveur MCP local (Claude Desktop/Code, transport
  stdio), volontairement non démarré automatiquement et non inclus dans
  l'image (voir `mcp_server/README.md`).
- Choix définitif de plateforme — délibérément laissé ouvert, voir
  checklist ci-dessus.

# Déploiement — squelette

Statut : **squelette non testé en conditions réelles**. Écrit sans démon
Docker disponible ni clés Meta/Claude configurées — à valider avant tout
déploiement réel (voir checklist en bas).

## Fichiers

- `Dockerfile` — image unique pour les deux surfaces web (pilote FastAPI
  `pilot_server.py` sur le port 8600, app Streamlit `app.py` sur le port
  8501), qui partagent le même code et les mêmes dépendances
  (`requirements.txt`). Le service lancé dépend de la commande (CMD par
  défaut : le pilote).
- `docker-compose.yml` — orchestration locale/VPS des deux services à
  partir de la même image. Pas encore lié à une plateforme précise
  (Fly.io, Render, VPS...).
- `.dockerignore` — exclut secrets locaux (`.env`), état runtime
  (`.lrs_*.json`, `.lrs_*.db`) et caches de l'image.

## Persistance des données — limitation connue

`app.py` et `pilot_server.py` écrivent leur état (historique, projets,
planification, etc. — voir `PILOT_UI.md`) dans des fichiers `.lrs_*.json`
situés **à côté du code**, pas dans un répertoire de données dédié. Le
Creative Studio ajoute `.lrs_creative_studio.db` (SQLite) au même endroit.

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
- [ ] SMTP (`SMTP_HOST/PORT/USER/PASSWORD`) si les emails (rapport
      d'audit, alertes monitoring, digest) doivent être envoyés
      (`email_alerts.py`).
- [ ] `STRIPE_WEBHOOK_SECRET` si le service de diffusion Creative Studio
      doit vérifier des paiements réels.
- [ ] Healthcheck : `GET /api/health` (pilote) répond `{"status":"ok"}`
      sans authentification, même si `APP_PASSWORD` est défini — à
      brancher sur le mécanisme de la plateforme (Docker `HEALTHCHECK`,
      load balancer...).
- [ ] Reverse proxy / TLS devant les deux ports (8501 Streamlit, 8600
      pilote) si exposés publiquement — aucun des deux ne sert de TLS
      lui-même.
- [ ] Sauvegarde du volume de données une fois la persistance résolue
      (historique d'audits, base Creative Studio).

## Hors périmètre de ce squelette

- `mcp_server/` — serveur MCP local (Claude Desktop/Code, transport
  stdio), volontairement non démarré automatiquement et non inclus dans
  l'image (voir `mcp_server/README.md`).
- Choix définitif de plateforme — délibérément laissé ouvert, voir
  checklist ci-dessus.

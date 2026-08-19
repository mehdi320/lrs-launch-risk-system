# Pilote UI Apple-style — les 8 onglets

Frontend custom (HTML/CSS/JS, sans framework) branché sur la même logique
d'audit que l'app Streamlit, pour évaluer un rendu "Apple-style" avant de
décider d'une migration plus large. Huit onglets, navigation via une barre
d'onglets en haut de page : Dashboard, Audit, Multi-Audit, Suivi,
Historique, Ressources, Creative Studio, Plans. Les onglets Multi-Audit,
Suivi, Ressources et Creative Studio ont chacun une sous-navigation
(deuxième niveau d'onglets) pour leurs sous-fonctionnalités.

## Fichiers

- `audit_engine.py` — logique d'audit extraite de `app.py` (extraction de
  page, scoring, génération d'angles créatifs). Copie autonome pour
  l'instant : si la migration est confirmée, `app.py` importera d'ici au
  lieu de dupliquer.
  `run_audit()` — le point d'entrée public, signature inchangée — bascule
  automatiquement vers **Claude** (`_run_audit_claude`, squelette) dès
  qu'`ANTHROPIC_API_KEY` est configurée ; sans cette clé, retombe sur
  **OpenAI** (`_run_audit_openai`, comportement historique inchangé). Les
  deux partagent le même prompt (`_build_audit_prompt`) et le même parsing
  de sortie (`_parse_audit_json`), donc le score ne dépend pas du moteur.
  Non encore testé avec une vraie clé Anthropic (échoue proprement avec un
  message clair tant que la clé n'est pas ajoutée — même pattern que les
  autres clés API du projet).
- `resources_content.py` — contenu statique de Ressources (Ads Library,
  Changelog, Benchmark), extrait de `app.py` pour être servi en JSON.
- `ads_api.py` — connecteurs Meta Ads / TikTok Ads (`fetch_meta_campaigns`,
  `fetch_tiktok_campaigns`) et corrélation stats pub × score LRS
  (`correlate_stats`), extraits de `app.py`.
- `integrations.py` — intégrations sortantes (Slack, Google Sheets,
  Notion), extraites de `app.py`. Lisent les mêmes variables d'env que
  l'app Streamlit (`SLACK_WEBHOOK_URL`, `GOOGLE_SHEETS_CREDS`, etc.).
- `jsonstore.py` — petit utilitaire `load_json_file`/`save_json_file`
  partagé par tous les fichiers d'état JSON.
- `email_alerts.py` — envoi d'emails SMTP (rapport d'audit, alerte chute de
  score, digest de monitoring), extrait de `app.py`. Chaque fonction accepte
  un `smtp_config` optionnel ; à défaut elle lit `SMTP_HOST/PORT/USER/
  PASSWORD` dans l'environnement. `app.py` lui passe son propre
  `_get_smtp_config()` (qui lit aussi `st.secrets` sur Streamlit Cloud) pour
  garder ce comportement sans le dupliquer.
- `pilot_server.py` — API FastAPI qui sert aussi le frontend statique.
  Endpoints principaux (voir le fichier pour la liste complète) :
  audit (`/api/audit`, `/api/bulk-audit`, `/api/compare`, `/api/abtests/*`),
  état partagé (`/api/dashboard`, `/api/history*`, `/api/alerts`,
  `/api/projects*`, `/api/campaigns*`, `/api/ads-connector/*`,
  `/api/swipefiles*`), contenu (`/api/resources/*`), sortie
  (`/api/export/pdf`, `/api/integrations/*`, `/api/plans`), Creative Studio
  réel (`/api/creative-studio/generate`), authentification
  (`/api/auth/login`, `/api/auth/status`, `/api/auth/logout`), onboarding
  (`/api/onboarding/status`, `/api/onboarding/complete`), monitoring
  planifié (`/api/monitoring/schedule*`, `/api/monitoring/check`).

  Persiste chaque audit (simple, bulk, comparaison, A/B, projet) dans
  `.lrs_history.json` — le même fichier que lit/écrit l'app Streamlit
  (`app.py::HISTORY_FILE`). Idem pour projets (`.lrs_projects.json`),
  campagnes (`.lrs_campaigns.json`), tests A/B (`.lrs_abtests.json`),
  swipe files (`.lrs_swipefiles.json`), identifiants API pub
  (`.lrs_ads_creds.json`), audits planifiés (`.lrs_schedule.json`) et statut
  d'onboarding (`.lrs_onboarded.json`) — état entièrement partagé entre les
  deux UIs.
- `pilot_static/index.html` — le frontend (une seule page, tout inclus,
  huit vues togglées en JS, avec sous-navigation pour certaines).

## Lancer en local

```bash
pip install -r requirements.txt   # fastapi/uvicorn déjà dedans
uvicorn pilot_server:app --port 8600 --reload
```

Ouvrir http://localhost:8600 — indépendant de l'app Streamlit (`streamlit
run app.py`), les deux peuvent tourner en parallèle sur des ports différents.

Nécessite `OPENAI_API_KEY` dans `.env` pour l'Audit/Multi-Audit/Creative
Studio (angles rapides). Le Studio avancé (Claude) nécessite en plus
`ANTHROPIC_API_KEY`. Les intégrations (Slack/Sheets/Notion) et la
Connexion API Pub (Meta/TikTok) nécessitent leurs propres identifiants —
tout échoue proprement avec un message clair tant que ces clés ne sont
pas configurées (même pattern que pour `OPENAI_API_KEY`).

Variables optionnelles : `APP_PASSWORD` (active le mot de passe d'accès),
`APP_SECRET_KEY` (clé de session fixe — recommandé en prod pour survivre
aux redémarrages, sinon générée aléatoirement au démarrage),
`SMTP_HOST/PORT/USER/PASSWORD` (emails), `LRS_ALERT_EMAIL` (email d'alerte
par défaut pour les audits planifiés sans email dédié) et
`LRS_DIGEST_EMAIL` (digest hebdomadaire des pages surveillées).

Un squelette Docker (`Dockerfile`, `docker-compose.yml`) existe pour faire
tourner le pilote et l'app Streamlit ensemble — voir `DEPLOYMENT.md` pour
son statut (non testé) et la checklist avant un vrai déploiement.

## Ce qui est couvert

- **Accès** : mot de passe partagé (`APP_PASSWORD`) via une session cookie
  (`starlette.SessionMiddleware`), même modèle qu'`app.py::check_access()` —
  pas de comptes multi-utilisateurs, pas de facturation intégrée (la
  monétisation reste externe via un lien Lemon Squeezy qui donne le mot de
  passe). Sans `APP_PASSWORD` défini, l'accès reste libre (mode dev).
- **Onboarding** : bandeau de bienvenue (3 étapes + liste des
  fonctionnalités) affiché tant que `.lrs_onboarded.json` n'existe pas,
  identique en contenu à `app.py::render_onboarding_banner()`.
- **Audit** : formulaire URL/pub, plateforme, type d'offre, marque, 3 modes
  (Funnel Only / Ads Only / Full Risk). Résultats complets (score, barres,
  raisons, action prioritaire, quick wins, rewrite).
- **Dashboard** : KPIs, streak + prochain objectif, pages en danger,
  évolution des scores, derniers audits.
- **Multi-Audit** :
  - *Bulk* — jusqu'à 20 URLs, podium top 3, tableau trié par score.
  - *Comparaison* / *Concurrents* — 2 URLs auditées côte à côte, breakdown
    comparatif (même endpoint `/api/compare`, cadrage différent).
  - *A/B Test* — scorer 2 variantes (URLs, mode Funnel Only dans les deux
    cas) : une page de vente classique, ou un advertorial (article/récit
    avant redirection vers la vraie page de vente — le scoring s'adapte,
    aucune pénalité pour l'absence de stack d'offre/prix/garantie, normaux
    ici puisqu'ils sont sur la page suivante). Un même test garde un seul
    type sur toute sa durée (`test_type`, affiché en badge sur chaque test
    existant). Historique des rounds par test, taux de victoire A vs B.
- **Suivi** :
  - *Alertes* — variations de score ≥2 pts par URL.
  - *Monitoring* — Score Trend par page (sélecteur d'URL suivie, sparkline,
    premier/dernier score, progression) et gestion complète des audits
    planifiés (créer/lancer maintenant/activer-désactiver/supprimer, avec
    alerte email optionnelle sur chute de score). Pas de scheduler serveur
    permanent : comme `app.py`, qui vérifie les audits en retard une fois
    par session, le frontend appelle `/api/monitoring/check` une fois à
    l'ouverture du pilote.
  - *Projets* — grouper des URLs en funnel, auditer en 1 clic, score
    moyen + maillon faible.
  - *Campagnes* — stats pub saisies manuellement, diagnostics croisés
    stats × score LRS (CTR/CPC/ROAS/CPA), historique par snapshot.
  - *API Pub* — connexion Meta Ads / TikTok Ads (identifiants utilisateur),
    import automatique des campagnes.
- **Historique** : recherche/filtres, stats globales, sparkline, lignes
  dépliables avec export (.txt / PDF), copie du résumé, envoi Slack, et
  tracker de recommandations (checkboxes persistées en localStorage).
- **Ressources** :
  - *Checklist* pré-lancement (localStorage).
  - *Ads Library* — frameworks et guides par plateforme (Meta/TikTok/
    Google/Funnel Écom/Copywriting), rendu markdown-lite.
  - *Swipe Files* — bibliothèque de hooks/headlines/CTAs/angles, alimentée
    automatiquement après chaque audit + ajout manuel.
  - *Benchmark* — stats clés + téléchargement du rapport PDF.
  - *Changelog* — historique des versions.
- **Creative Studio** :
  - *Angles rapides* — 3 angles, 5 hooks, 3 variantes, script UGC via
    OpenAI, à partir d'une description d'offre.
  - *Studio avancé (Claude)* — génération structurée (headline, hook,
    corps, CTA) par framework (PAS/AIDA/Hormozi), via le vrai module
    `creative_studio/core/copy_generation.py` (Claude).
- **Plans** : page informative des 4 plans (Free/Starter/Pro/Agency),
  usage du mois courant, statut des intégrations (Slack/Sheets/Notion).

Tout l'état (historique, projets, campagnes, tests A/B, swipe files,
identifiants API pub) est partagé avec l'app Streamlit via les mêmes
fichiers JSON.

## Ce qui n'est PAS encore couvert

- **Multi-Audit** : import CSV pour le Bulk.
- **Historique** : export CSV côté serveur (fait en JS côté client à la
  place), tracker d'implémentation partagé entre utilisateurs (actuellement
  en localStorage, donc local au navigateur).
- **Comptes / facturation** : comme dans `app.py`, il n'y a qu'un mot de
  passe partagé (pas de comptes individuels ni de paiement intégré) — la
  page Plans reste informative, sans enforcement des quotas.
- Drip emails, white-label — fonctionnalités secondaires de l'app Streamlit
  non reprises dans cette v1.

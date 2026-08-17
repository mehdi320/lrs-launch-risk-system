# Pilote UI Apple-style — les 7 onglets

Frontend custom (HTML/CSS/JS, sans framework) branché sur la même logique
d'audit que l'app Streamlit, pour évaluer un rendu "Apple-style" avant de
décider d'une migration plus large. Sept onglets, navigation via une barre
d'onglets en haut de page : Dashboard, Audit, Multi-Audit, Suivi,
Historique, Ressources, Creative Studio.

## Fichiers

- `audit_engine.py` — logique d'audit extraite de `app.py` (extraction de
  page, appel OpenAI, scoring, génération d'angles créatifs). Copie
  autonome pour l'instant : si la migration est confirmée, `app.py`
  importera d'ici au lieu de dupliquer.
- `pilot_server.py` — API FastAPI qui sert aussi le frontend statique :
  - `POST /api/audit` — lance un audit (Funnel Only / Ads Only / Full Risk)
  - `GET /api/dashboard` — KPIs + résumé pour l'onglet Dashboard
  - `GET /api/history` — liste filtrable (recherche, risque, plateforme)
  - `GET /api/alerts` — variations de score significatives par URL
  - `POST /api/bulk-audit` — audite jusqu'à 20 URLs séquentiellement
  - `POST /api/creative-angles` — génère angles/hooks/variantes/script UGC
    à partir d'une description d'offre (sans landing page)

  Persiste chaque audit (simple ou bulk) dans `.lrs_history.json`, le même
  fichier que lit/écrit l'app Streamlit (`app.py::HISTORY_FILE`) —
  historique partagé entre les deux UIs.
- `pilot_static/index.html` — le frontend (une seule page, tout inclus,
  sept vues togglées en JS).

## Lancer en local

```bash
pip install -r requirements.txt   # fastapi/uvicorn déjà dedans
uvicorn pilot_server:app --port 8600 --reload
```

Ouvrir http://localhost:8600 — indépendant de l'app Streamlit (`streamlit
run app.py`), les deux peuvent tourner en parallèle sur des ports différents.

Nécessite `OPENAI_API_KEY` dans `.env` (même variable que l'app Streamlit).
Sans clé configurée, les formulaires fonctionnent mais les appels réels
échoueront avec un message clair — utilisez le lien **"Voir un exemple"**
sous le bouton d'Audit pour prévisualiser le rendu des résultats avec des
données de démo, sans appel API.

## Ce qui est couvert (v1, périmètre volontairement réduit — "cœur simplifié")

- **Audit** : formulaire URL/pub, plateforme, type d'offre, marque
  (contrôles segmentés façon iOS/macOS), 3 modes (Funnel Only / Ads Only /
  Full Risk). Résultats : score animé, barres Hook/Offer/Trust/Friction,
  verdict, raisons du score, action prioritaire, quick wins, rewrite
  suggéré.
- **Dashboard** : KPIs (audits total, score moyen, meilleur score, pages en
  danger, prêtes à scaler), streak + prochain objectif, pages en danger
  immédiat, évolution des scores (sparkline SVG, derniers 10 audits),
  derniers audits.
- **Multi-Audit** : liste d'URLs (une par ligne, 20 max), audite chacune
  séquentiellement (Funnel Only / Full Risk), podium top 3, tableau de
  résultats trié par score, liste des échecs d'extraction.
- **Suivi** : alertes de variation de score (≥2 pts) par URL entre deux
  audits successifs, triées par amplitude.
- **Historique** : liste complète et filtrable (recherche texte, risque,
  plateforme), bannière de progression globale (delta / score moyen /
  total), sparkline d'évolution, chaque ligne dépliable (décision,
  plateforme, risque, delta vs précédent).
- **Ressources** : checklist pré-lancement (5 catégories, 20 items),
  cases à cocher persistées en localStorage, barre de progression avec
  seuils (rouge <50%, orange <80%, vert 80%+).
- **Creative Studio** : génère 3 angles publicitaires, 5 hooks, 3 variantes
  de pub et un script UGC 20s à partir d'une description d'offre — réutilise
  l'infra OpenAI déjà configurée (pas de dépendance au vrai module
  `creative_studio/` qui utilise Claude/Anthropic + une base de données).

Tous les audits (simples, bulk) et l'historique sont partagés avec l'app
Streamlit via `.lrs_history.json`.

## Ce qui n'est PAS encore couvert

- **Multi-Audit** : Comparaison 2 pages, Audit Concurrents, A/B Test tracker.
- **Suivi** : Projets, Campagnes en cours, Connexion API Pub.
- **Historique** : export, tracker d'implémentation par audit.
- **Ressources** : Ads Library, Mes Swipe Files, Benchmark 2025, Changelog.
- **Creative Studio réel** : le vrai module (`creative_studio/`) génère des
  advertorials/pages de vente complets via Claude, avec stockage en base,
  A/B testing et séquences email — hors périmètre de cette v1, qui ne
  couvre que la génération d'angles/hooks.
- Export PDF/txt, partage, intégrations, quotas/plans, comparaison
  avant/après — tout ce qui existe déjà dans l'app Streamlit au-delà du
  cœur couvert ci-dessus. À ajouter au fur et à mesure si le pilote est
  validé.

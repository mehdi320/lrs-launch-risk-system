# Pilote UI Apple-style — Dashboard + Audit

Frontend custom (HTML/CSS/JS, sans framework) branché sur la même logique
d'audit que l'app Streamlit, pour évaluer un rendu "Apple-style" avant de
décider d'une migration plus large. Deux onglets pour l'instant : Dashboard
et Audit, navigation via une barre d'onglets en haut de page.

## Fichiers

- `audit_engine.py` — logique d'audit extraite de `app.py` (extraction de
  page, appel OpenAI, scoring). Copie autonome pour l'instant : si la
  migration est confirmée, `app.py` importera d'ici au lieu de dupliquer.
- `pilot_server.py` — API FastAPI (`POST /api/audit`, `GET /api/dashboard`)
  qui sert aussi le frontend statique. Persiste chaque audit dans
  `.lrs_history.json`, le même fichier que lit/écrit l'app Streamlit
  (`app.py::HISTORY_FILE`) — historique partagé entre les deux UIs.
- `pilot_static/index.html` — le frontend (une seule page, tout inclus,
  deux vues togglées en JS : Dashboard et Audit).

## Lancer en local

```bash
pip install -r requirements.txt   # fastapi/uvicorn déjà dedans
uvicorn pilot_server:app --port 8600 --reload
```

Ouvrir http://localhost:8600 — indépendant de l'app Streamlit (`streamlit
run app.py`), les deux peuvent tourner en parallèle sur des ports différents.

Nécessite `OPENAI_API_KEY` dans `.env` (même variable que l'app Streamlit).
Sans clé configurée, le formulaire fonctionne mais l'audit réel échouera —
utilisez le lien **"Voir un exemple"** sous le bouton pour prévisualiser le
rendu des résultats avec des données de démo, sans appel API.

## Ce qui est couvert (v1, périmètre volontairement réduit)

- **Audit** : formulaire URL/pub, plateforme, type d'offre, marque
  (contrôles segmentés façon iOS/macOS), 3 modes (Funnel Only / Ads Only /
  Full Risk). Résultats : score animé, barres Hook/Offer/Trust/Friction,
  verdict, raisons du score, action prioritaire, quick wins, rewrite
  suggéré.
- **Dashboard** : KPIs (audits total, score moyen, meilleur score, pages en
  danger, prêtes à scaler), streak + prochain objectif, pages en danger
  immédiat, évolution des scores (sparkline SVG, derniers 10 audits),
  derniers audits. Reflète en temps réel les audits lancés depuis le
  pilote ou depuis l'app Streamlit (fichier d'historique partagé).

## Ce qui n'est PAS encore couvert

Multi-Audit, Suivi, Historique complet (recherche/filtre/export),
Ressources, Creative Studio, export PDF/txt, partage, intégrations,
quotas/plans, comparaison avant/après, quick wins du dernier audit et
checklist d'activation sur le Dashboard — tout ce qui existe déjà dans
l'app Streamlit au-delà du cœur couvert ci-dessus. À ajouter au fur et à
mesure si le pilote est validé.

# Pilote UI Apple-style — onglet Audit

Frontend custom (HTML/CSS/JS, sans framework) branché sur la même logique
d'audit que l'app Streamlit, pour évaluer un rendu "Apple-style" avant de
décider d'une migration plus large.

## Fichiers

- `audit_engine.py` — logique d'audit extraite de `app.py` (extraction de
  page, appel OpenAI, scoring). Copie autonome pour l'instant : si la
  migration est confirmée, `app.py` importera d'ici au lieu de dupliquer.
- `pilot_server.py` — API FastAPI (`POST /api/audit`) qui sert aussi le
  frontend statique.
- `pilot_static/index.html` — le frontend (une seule page, tout inclus).

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

- Formulaire : URL, plateforme, type d'offre, marque (contrôles segmentés
  façon iOS/macOS).
- Extraction de la page + appel OpenAI (mode Funnel Only uniquement pour
  l'instant).
- Résultats : score animé, barres Hook/Offer/Trust/Friction, verdict,
  raisons du score, action prioritaire, quick wins, rewrite suggéré.

## Ce qui n'est PAS encore couvert

Ads Only / Full Risk, historique, export PDF/txt, partage, intégrations,
quotas/plans, comparaison avant/après — tout ce qui existe déjà dans
l'onglet Audit Streamlit au-delà du cœur "URL → score". À ajouter si le
pilote est validé et qu'on part sur la migration complète.

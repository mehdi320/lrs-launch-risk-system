# Tester LRS en local

Le pilote est une app FastAPI (`pilot_server.py`) servie par uvicorn. L'ancienne
app Streamlit (`app.py`) n'existe plus.

## 1. Installer les dépendances

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Configurer `.env`

Copiez `.env.example` en `.env`, puis choisissez un moteur pour les audits :

- **Claude (comme en prod)** : renseignez `ANTHROPIC_API_KEY=sk-ant-...`.
- **Ollama (gratuit, local)** : installez [Ollama](https://ollama.com), lancez
  `ollama pull qwen2.5:7b`, puis mettez `LLM_BACKEND=ollama` dans `.env`. Les
  audits et les Angles rapides passent alors par Ollama. Comptez 1 à 3 min par
  audit selon la machine. Le Studio avancé demande toujours une clé Claude.

`APP_PASSWORD` protège l'accès. Laissez-le vide pour un accès libre en local,
jamais en prod.

## 3. Lancer le pilote

```bash
venv\Scripts\python -m uvicorn pilot_server:app --port 8600
```

Ouvrez `http://localhost:8600`.

## 4. Premier test

1. Onglet **Audit**, mode **Ads Only**, plateforme **Meta**.
2. Collez ce texte de pub :

   ```
   Tu bosses 40h/semaine mais tu stagnes à 3000€/mois ?
   J'étais exactement là il y a 18 mois.
   Aujourd'hui je génère 8000€/mois en 25h.
   Voici le système exact, lien en bio.
   ```

3. Cliquez **Lancer l'audit**.

Si tout fonctionne, vous voyez :

- un score /20 et son détail (Hook / Offer / Trust / Friction) ;
- un verdict : Do NOT launch / Test small budget / Ready to scale ;
- les raisons du score, l'action prioritaire et les quick wins ;
- un rewrite (headline, sous-titre, CTA, garantie).

L'audit apparaît ensuite dans **Historique**, d'où on l'exporte en .txt ou PDF.

## Problèmes courants

| Message | Cause |
|---|---|
| « Clé API Claude manquante » | `ANTHROPIC_API_KEY` vide et `LLM_BACKEND` pas sur `ollama` |
| « Ollama injoignable » | l'app Ollama n'est pas lancée |
| « Modèle Ollama absent » | lancez `ollama pull qwen2.5:7b` |
| « Authentification requise » | `APP_PASSWORD` est défini : connectez-vous d'abord |

## Ensuite : mise en ligne

Suivez `DEPLOYMENT.md` (Docker + Caddy sur un VPS).

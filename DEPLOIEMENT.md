# 🚀 Déploiement LRS sur Streamlit Cloud — Guide Rapide

Streamlit Cloud = hébergement gratuit, en ligne en 5 minutes.

---

## Étape 1 — Mettre les fichiers sur GitHub

Crée un repo GitHub (public ou privé) avec ces fichiers :

```
lrs/
├── app.py
├── requirements.txt
├── .env.example
├── methodology_ecom.txt
├── methodology_digital.txt
├── concepts_funnels.txt
└── concepts_ads_meta_tiktok_google.txt
```

> ⚠️ Ne jamais mettre le fichier `.env` sur GitHub (il contient ta clé API).

---

## Étape 2 — Créer un compte Streamlit Cloud

Va sur → **https://share.streamlit.io**

Connecte-toi avec ton compte GitHub.

---

## Étape 3 — Déployer l'app

1. Clique **"New app"**
2. Sélectionne ton repo GitHub
3. Branch : `main`
4. Main file path : `app.py`
5. Clique **"Deploy"**

---

## Étape 4 — Ajouter ta clé API OpenAI

Une fois l'app déployée :

1. Clique sur **`⋮`** (trois points) en haut à droite de ton app
2. Va dans **"Settings"** → **"Secrets"**
3. Ajoute exactement ceci :

```toml
OPENAI_API_KEY = "sk-..."
```

4. Clique **"Save"** — l'app redémarre automatiquement.

---

## Résultat

Ton LRS est accessible à une URL du type :
`https://ton-pseudo-lrs.streamlit.app`

Tu peux la partager directement avec des clients ou utilisateurs.

---

## Coût estimé (OpenAI)

| Modèle | Coût par audit |
|--------|---------------|
| gpt-4o-mini | ~0.01 € |
| gpt-4o | ~0.10 € |

Streamlit Cloud = **gratuit** pour un usage normal.

---

## Test local avant déploiement

```bash
pip install -r requirements.txt
cp .env.example .env
# Ouvrir .env et mettre ta vraie clé
streamlit run app.py
```

---

## Problèmes courants

**"Clé API manquante"**
→ Vérifie que tu as bien ajouté la clé dans Streamlit Secrets (pas dans `.env`)

**"Fichier manquant : methodology_ecom.txt"**
→ Assure-toi que tous les fichiers `.txt` sont dans ton repo GitHub

**Extraction de page vide**
→ Certains sites bloquent les bots. Colle le contenu manuellement dans "Contexte optionnel"

---

## Déploiement avec abonnement Stripe (Docker + Caddy)

Streamlit Cloud (ci-dessus) ne peut héberger que `app.py` — pas de route HTTP
pour recevoir un webhook Stripe. Si vous voulez l'activation automatique de
compte à l'achat (au lieu de coller une licence à la main), il faut un VPS
avec Docker, qui fait tourner **trois** services : `app.py` (Streamlit),
`webhook_server.py` (FastAPI, checkout + webhook Stripe) et `caddy`
(reverse proxy, TLS Let's Encrypt automatique).

### 1. Prérequis

- Un VPS (ou une VM Google Cloud e2-micro, Always Free) avec Docker et
  Docker Compose installés
- Un nom de domaine, avec deux sous-domaines pointés en DNS (A record) vers
  l'IP du serveur : un pour l'app (`app.votre-domaine.com`), un pour l'API
  webhook (`api.votre-domaine.com`)
- Un compte Stripe, avec un produit/prix créé (mode Test pour valider
  d'abord, mode Live une fois prêt)

### 2. Configurer Stripe

1. Dashboard Stripe → Produits → créez le produit + prix de l'offre bêta,
   notez le `price_id`
2. Développeurs → Webhooks → **Add endpoint** :
   URL = `https://api.votre-domaine.com/webhook/stripe`, événements à
   écouter : `checkout.session.completed`, `customer.subscription.updated`,
   `customer.subscription.deleted`
3. Copiez la clé secrète (`sk_test_...` ou `sk_live_...`) et le secret de
   signature du endpoint (`whsec_...`)

### 3. Configurer `.env`

```bash
cp .env.example .env
```

Renseignez au minimum : `STRIPE_SECRET_KEY`, `STRIPE_PRICE_ID`,
`STRIPE_WEBHOOK_SECRET`, `LRS_APP_URL`, `LRS_APP_DOMAIN`, `LRS_API_DOMAIN`,
`SMTP_HOST`/`SMTP_USER`/`SMTP_PASSWORD` (pour l'envoi du lien magique).
Laissez `LRS_ALLOW_UNVERIFIED_WEBHOOK=false` en production.

### 4. Lancer

```bash
docker compose up -d --build
```

Caddy obtient automatiquement les certificats TLS pour les deux domaines au
premier démarrage (le DNS doit déjà pointer vers le serveur).

### 5. Tester avant d'exposer le vrai lien de paiement

```bash
# Terminal 1 — service webhook en mode non-vérifié
LRS_ALLOW_UNVERIFIED_WEBHOOK=true LRS_USERS_DB_PATH=/tmp/lrs_test.db \
  uvicorn webhook_server:app --port 8000

# Terminal 2 — la suite de tests (6 scénarios : activation, mise à jour,
# résiliation, event ignoré, rejeu dupliqué, échec puis retry)
python3 test_stripe_webhook.py
```

Avec le CLI Stripe (`stripe listen --forward-to localhost:8000/webhook/stripe`
puis `stripe trigger checkout.session.completed`), vous pouvez valider un
paiement réel en mode Test de bout en bout avant de passer en Live.

⚠️ Ne republiez le lien de paiement public qu'une fois le webhook réellement
joignable — un paiement reçu avant que `api.votre-domaine.com` ne réponde
manquerait l'activation automatique (récupérable manuellement en appelant
`user_accounts.upsert_user_from_checkout(...)` avec les infos du Dashboard
Stripe).

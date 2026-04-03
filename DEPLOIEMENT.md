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

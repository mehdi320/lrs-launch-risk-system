# ⚠️ LRS™ — Launch Risk System V1.2

**Paid Traffic Pre-Launch Audit Tool**

LRS™ est un outil d'audit pré-lancement pour les campagnes de paid traffic.
Il analyse vos landing pages, publicités (Meta / TikTok / Google), et la cohérence entre les deux pour vous donner un verdict de lancement basé sur un scoring structuré.

---

## 🚀 Installation Rapide

### 1. Prérequis

- Python 3.10+
- Une clé API OpenAI ([obtenir ici](https://platform.openai.com/api-keys))

### 2. Cloner / Télécharger le projet

```bash
# Si vous utilisez git
git clone <votre-repo>
cd lrs

# Ou simplement placez tous les fichiers dans un dossier lrs/
```

### 3. Créer un environnement virtuel

```bash
# Créer l'environnement
python -m venv venv

# Activer sur macOS / Linux
source venv/bin/activate

# Activer sur Windows
venv\Scripts\activate
```

### 4. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 5. Configurer la clé API

```bash
# Copier le fichier exemple
cp .env.example .env

# Ouvrir .env et remplacer la valeur
# OPENAI_API_KEY=sk-votre-vraie-cle-ici
```

### 6. Lancer l'application

```bash
streamlit run app.py
```

L'application s'ouvre automatiquement sur `http://localhost:8501`

---

## 📂 Structure du Projet

```
lrs/
├── app.py                          # Application principale Streamlit
├── requirements.txt                # Dépendances Python
├── .env.example                    # Template de configuration
├── .env                            # Votre config (à créer, non versionné)
├── methodology_ecom.txt            # Méthodologie scoring Ecom
├── methodology_digital.txt         # Méthodologie scoring Digital
├── concepts_funnels.txt            # Base de connaissances funnels / landing
├── concepts_ads_meta_tiktok_google.txt  # Base de connaissances ads
└── README.md
```

---

## 🎯 Les 3 Modes d'Audit

### Mode 1 — Funnel Only

**Quand l'utiliser :** Vous avez une landing page existante et voulez savoir si elle est prête pour le paid traffic.

**Ce que vous fournissez :**
- URL de la landing page

**Ce que vous obtenez :**
- Score global /20
- Breakdown sur 4 axes (Hook, Offer, Trust, Friction)
- Risk level + Launch decision
- Estimation CVR actuel et post-fix
- Plan d'action priorisé
- Rewrite complet (headline, bullets, CTA, offer stack, garantie, FAQ)
- Recommandations d'ads pour matcher la page

---

### Mode 2 — Ads Only

**Quand l'utiliser :** Vous avez un script ou texte de pub et voulez l'évaluer avant de lancer.

**Ce que vous fournissez :**
- Script / texte de la publicité
- Plateforme (Meta / TikTok / Google / Mixed)

**Ce que vous obtenez :**
- Score global /20
- Angles publicitaires recommandés
- Hooks alternatifs
- 3 variantes d'ads (primary text + headline + CTA)
- Script UGC 20-30 secondes
- Recommandations de landing page alignée

---

### Mode 3 — Full Risk (Recommandé)

**Quand l'utiliser :** Avant tout lancement de campagne payante. C'est le mode le plus complet.

**Ce que vous fournissez :**
- URL de la landing page
- Script / texte de la publicité
- Plateforme
- Type d'offre (Ecom / Digital)
- Contexte optionnel (cible, budget, AOV...)

**Ce que vous obtenez :**
- Score global /20
- Verdict de lancement : **Do NOT launch** / **Test small budget** / **Ready to scale**
- Analyse de message match complète
- Mismatches identifiés + corrections
- CVR estimé actuel et post-fix
- Plan d'action priorisé avec effort/impact
- A/B tests recommandés
- Rewrite complet landing + nouvelles variantes d'ads

---

## 📊 Logique de Scoring

### Les 4 axes (/5 chacun = 20 total)

| Axe | Ce qu'il mesure |
|-----|-----------------|
| **Hook** | Force du premier contact (headline, image hero, opening line de la pub) |
| **Offer** | Clarté, valeur perçue, stack, garantie, prix |
| **Trust** | Social proof, témoignages, crédibilité, badges |
| **Friction / Message Match** | Fluidité du parcours, cohérence pub↔landing |

### Décisions de lancement

| Score | Decision | Risk Level | Action recommandée |
|-------|----------|-----------|-------------------|
| 0 – 9 | 🚫 Do NOT launch | HIGH | Corriger les fondamentaux |
| 10 – 14 | ⚠️ Test small budget | MODERATE | $50-200/j max, valider d'abord |
| 15 – 20 | ✅ Ready to scale | LOW | Scaling progressif possible |

---

## ⚙️ Configuration Avancée

### Modèles OpenAI

| Modèle | Vitesse | Coût | Recommandé pour |
|--------|---------|------|-----------------|
| `gpt-4o-mini` | Rapide | ~$0.01/audit | Usage quotidien |
| `gpt-4o` | Modéré | ~$0.10/audit | Audits critiques |

### Fichiers de méthodologie

Les fichiers `.txt` sont la **source de vérité** du système de scoring.
Vous pouvez les modifier pour adapter la méthodologie à votre marché ou vos standards.

- `methodology_ecom.txt` — Framework scoring produits physiques
- `methodology_digital.txt` — Framework scoring produits digitaux
- `concepts_funnels.txt` — Principes de conversion landing pages
- `concepts_ads_meta_tiktok_google.txt` — Principes créatifs publicitaires

---

## 📝 Exemple d'Usage

### Scénario : Lancer une campagne Meta pour une formation en ligne à 297€

1. **Mode :** Full Risk
2. **Plateforme :** Meta
3. **Type d'offre :** Digital product
4. **URL :** `https://maformation.com/landing`
5. **Script pub :**
   ```
   Tu bosses 40h/semaine mais tu stagnes à 3000€/mois ?
   J'étais exactement là il y a 18 mois.
   Aujourd'hui je génère 8000€/mois en 25h.
   Voici le système exact — lien en bio.
   ```
6. **Contexte :** `Cible : freelances 28-45 ans / Formation copywriting / AOV 297€ / Budget test 500€/sem`

**Résultat attendu :** Score /20 + verdict + plan d'action spécifique à ce scénario.

---

## ⚠️ Disclaimers

- Les estimations CVR sont indicatives et non garanties
- Les performances réelles dépendent de nombreux facteurs (audience, budget, concurrence, timing)
- LRS™ est un outil d'aide à la décision, pas un oracle
- Ne lancez jamais une campagne sans tester sur petit budget d'abord

---

## 🐛 Problèmes Courants

**"Clé API manquante"**
→ Vérifiez que votre fichier `.env` existe et contient `OPENAI_API_KEY=sk-...`

**"Impossible de se connecter à l'URL"**
→ Vérifiez que l'URL est accessible publiquement et commence par `https://`

**"Fichier manquant : methodology_ecom.txt"**
→ Assurez-vous que tous les fichiers .txt sont dans le même dossier que `app.py`

**L'extraction de page est vide ou partielle**
→ Certains sites bloquent les bots. Essayez de coller manuellement le contenu dans le champ "Contexte optionnel"

---

*LRS™ V1.2 — Build with Streamlit + OpenAI*

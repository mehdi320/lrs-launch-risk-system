# 🧪 Tester LRS en local — Guide pas à pas

## Étape 1 — Remplacer tes fichiers

Dans ton dossier LRS, remplace les fichiers existants par les versions du dossier outputs :

```
app.py           ← nouveau fichier (V2.1 OpenAI)
requirements.txt ← nouveau fichier (avec openai + python-dotenv)
```

Les fichiers `.txt` (methodology_ecom, methodology_digital, concepts_funnels, concepts_ads)
**ne changent pas** — garde les tels quels.

---

## Étape 2 — Installer les nouvelles dépendances

Ouvre ton terminal dans le dossier LRS :

```bash
# Si tu as un venv, active-le d'abord
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

# Installer les dépendances
pip install -r requirements.txt
```

---

## Étape 3 — Configurer ta clé API OpenAI

1. Ouvre le fichier `.env` (crée-le s'il n'existe pas)
2. Ajoute ta clé :

```
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxx
```

> Obtenir une clé : https://platform.openai.com/api-keys
> Coût estimé pour tester : < 0.10€ pour 10 audits avec gpt-4o-mini

---

## Étape 4 — Lancer l'app

```bash
streamlit run app.py
```

L'app s'ouvre sur `http://localhost:8501`

---

## Étape 5 — Faire un premier test

### Test rapide (Ads Only)

1. Mode : **Ads Only**
2. Plateforme : **Meta**
3. Type d'offre : **Digital product**
4. Modèle : **gpt-4o-mini** (rapide et pas cher)
5. Colle ce script de test :

```
Tu bosses 40h/semaine mais tu stagnes à 3000€/mois ?
J'étais exactement là il y a 18 mois.
Aujourd'hui je génère 8000€/mois en 25h.
Voici le système exact — lien en bio.
```

6. Clique **Run LRS Audit**
7. Résultat en ~15 secondes

---

### Test complet (Full Risk)

1. Mode : **Full Risk**
2. Remplis : URL d'une vraie landing page + script pub
3. Modèle : **gpt-4o** pour plus de précision
4. Clique **Run LRS Audit**

---

## Ce que tu dois voir si tout fonctionne ✅

- Score /20 avec breakdown (Hook / Offer / Trust / Friction)
- Verdict : Do NOT launch / Test small budget / Ready to scale
- Analyse détaillée de chaque axe
- Plan d'action avec priorités
- Rewrite (headline, CTA, bullets, garantie)
- Bouton "Exporter .txt"

---

## Problèmes courants

**"Clé API manquante"**
→ Vérifie que `.env` existe et contient `OPENAI_API_KEY=sk-...`

**"ModuleNotFoundError: No module named 'openai'"**
→ Relance `pip install -r requirements.txt`

**"Rate limit"**
→ Attends 10 secondes et relance l'audit

**"Quota OpenAI épuisé"**
→ Va sur platform.openai.com → Billing → ajoute du crédit (5€ suffisent pour 500 audits)

---

## Une fois satisfait du test → Déploiement en ligne

Suis le guide `DEPLOIEMENT.md` pour mettre LRS accessible en ligne via Streamlit Cloud.

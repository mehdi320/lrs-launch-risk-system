# LRS — Contenu statique de l'onglet Ressources (Checklist, Ads Library, Changelog, Benchmark)
#
# Extrait de app.py (render_checklist, render_ads_library, render_changelog,
# render_benchmark_tab) pour être consommé à la fois par l'app Streamlit et
# par pilot_server.py, sans dupliquer le contenu texte dans les deux endroits.

CHECKLIST = [
    ("Hook & Headline", [
        "La headline repond clairement : qu'est-ce que j'obtiens ?",
        "La headline contient un chiffre, timeframe ou persona specifique",
        "L'image hero montre le produit en action ou le resultat visible",
        "Le visiteur comprend la valeur en moins de 5 secondes",
    ]),
    ("Offre", [
        "Le prix est visible sans scroller",
        "Il y a un offer stack avec valeurs chiffrees",
        "La garantie est visible directement sous le CTA principal",
        "Il y a une urgence ou rarete credible",
    ]),
    ("Trust", [
        "Il y a au moins 10 avis ou temoignages",
        "Les temoignages ont prenom + resultat specifique",
        "Il y a un badge de paiement securise visible",
        "Le nombre total d'acheteurs est mentionne",
    ]),
    ("Friction & CTA", [
        "Il y a un seul CTA principal",
        "Le CTA est repete au moins 3 fois sur la page",
        "Pas de menu de navigation distrayant",
        "Le parcours d'achat fait moins de 3 clics",
    ]),
    ("Tracking", [
        "Le Pixel Meta ou TikTok est installe et verifie",
        "L'evenement Purchase est configure",
        "Google Analytics est actif",
        "Un test d'achat a ete effectue",
    ]),
]

ADS_LIBRARY = {
    "meta": {
        "label": "Meta Ads",
        "cards_heading": "Frameworks rapides", "guides_heading": "Guide complet Meta Ads",
        "cards": [
            {
                "title": "Hook Formula — 4 types", "color": "accent", "icon": "🎯",
                "items": [
                    "Question : « Pourquoi vos pubs Meta ne convertissent pas ? »",
                    "Stat choc : « 73% des campagnes échouent dès J1 — voici pourquoi »",
                    "Pattern interrupt : visuel inattendu + texte court",
                    "Identification : « Si tu fais du paid traffic... »",
                ],
            },
            {
                "title": "Structure pub Meta", "color": "success", "icon": "📐",
                "items": [
                    "0–3s : Hook visuel + texte overlay (une phrase max)",
                    "3–15s : Corps — problème → solution → preuve",
                    "15–30s : CTA clair + urgence (« Offre se termine dimanche »)",
                    "Primary text : 125 car. avant « Voir plus » → hook obligatoire",
                ],
            },
            {
                "title": "Benchmarks CTR (cold traffic)", "color": "warning", "icon": "📊",
                "items": [
                    "> 2% CTR : bon — publiez davantage",
                    "> 4% CTR : excellent — scalez le budget",
                    "< 1% CTR : créa à revoir ou audience trop large",
                    "CPM acceptable : 8–18€ (FR, ecom/digital)",
                    "Fréquence > 3.5 : creative fatigue, changez la créa",
                ],
            },
            {
                "title": "Modèles de primary text", "color": "cyan", "icon": "✍️",
                "items": [
                    "PAS : Problème → Agitate (« tu perds X€/j ») → Solve",
                    "Social Proof : « [Prénom] a obtenu [résultat] en [durée] »",
                    "Direct : « [Bénéfice] sans [douleur] — voici comment »",
                    "Question + Réponse : « Tu veux X ? Voilà ce que font les pros »",
                ],
            },
        ],
        "guides": [
            {"title": "🎯 Stratégie d'audiences — de zéro à scale", "body": """**Phase 1 — Testing cold traffic**
- Broad (sans intérêts) sur comportements d'achat larges — budget 20€/j par adset
- Lookalike 1-3% sur vos meilleurs acheteurs (LAL)
- 1-2 intérêts larges très ciblés (pas les intérêts évidents)

**Phase 2 — Scale ce qui marche**
- ROAS > 2.5 → doublez le budget tous les 3 jours max (pas tous les jours)
- CBO (Campaign Budget Optimization) une fois que vous avez 2+ adsets gagnants
- Évitez de toucher une adset active les 3 premiers jours — laissez l'algo apprendre

**Phase 3 — Retargeting**
- Visiteurs 7j non-acheteurs : montrez les preuves sociales (reviews, résultats)
- ATC 14j non-acheteurs : urgence + offre légèrement différente
- Acheteurs 180j : upsell / cross-sell — CPM ultra-bas, ROAS élevé"""},
            {"title": "📐 Formats créatifs gagnants en 2025", "body": """**Image statique avec texte overlay** (fonctionne toujours)
- Fond simple ou produit seul — texte blanc sur fond sombre
- La règle : 1 image = 1 message = 1 CTA
- Ratio 1:1 pour Feed, 9:16 pour Stories/Reels

**UGC 15–30s** (meilleur ROAS actuellement)
- Personne réelle face caméra, son naturel, tenue décontractée
- Structure : pain point 0-3s → solution → démonstration → résultat
- Pas de musique de fond, pas de logo au début — must feel native

**Reels natifs avec voiceover**
- Tendances visuelles TikTok adaptées à Meta
- Hook textuel sur les 2 premières secondes
- Sous-titres obligatoires (85% regardent sans son)

**Carousel ecom**
- Slide 1 : bénéfice principal (pas le produit)
- Slides 2-4 : preuves, features, résultats
- Slide finale : CTA + offre"""},
            {"title": "⚙️ Structure de compte optimale", "body": """**Structure recommandée 2025 :**
```
Campagne CBO — [Objectif : Ventes]
  +-- Adset 1 : Broad 18-45 (pas d'intérêts)
  +-- Adset 2 : LAL 1-3% acheteurs
  +-- Adset 3 : Intérêt large #1
      +-- Créa A (image statique)
      +-- Créa B (UGC 15s)
      +-- Créa C (Reels natif)
```

**Règles d'or :**
- 1 campagne Prospection + 1 campagne Retargeting (séparées !)
- Minimum 3 créas par adset pour donner de l'espace à l'algo
- Ne changez pas le budget de + 20% en une seule fois — reset la phase d'apprentissage
- Pixel : Event Purchase obligatoire avant de lancer (conversion event)"""},
        ],
    },
    "tiktok": {
        "label": "TikTok Ads",
        "cards_heading": "Frameworks rapides", "guides_heading": "Guide complet TikTok Ads",
        "cards": [
            {
                "title": "La règle des 2 premières secondes", "color": "tiktok", "icon": "⚡",
                "items": [
                    "Le scroll dure 0.5s — votre hook doit arrêter le pouce",
                    "✅ Visuel inattendu OU texte choc en overlay immédiat",
                    "✅ Commencer IN MEDIAS RES (milieu d'action)",
                    "❌ Logo au début = skip garanti",
                    "❌ Intro lente avec musique = perte d'audience",
                ],
            },
            {
                "title": "Structure vidéo TikTok Ads", "color": "tiktok", "icon": "📱",
                "items": [
                    "0-2s : Hook visuel + texte (pattern interrupt)",
                    "2-8s : Problème ou identification (« Si tu fais X... »)",
                    "8-18s : Solution + démonstration rapide",
                    "18-25s : Preuve sociale (before/after, témoignage)",
                    "25-30s : CTA clair + urgence",
                ],
            },
            {
                "title": "Benchmarks TikTok Ads", "color": "success", "icon": "📊",
                "items": [
                    "✅ CTR > 2.5% : bon pour cold traffic",
                    "✅ CPM : 5–12€ (FR) — plus bas que Meta",
                    "⚠️ VTR (View-Through Rate) > 25% à 6s : hook OK",
                    "🚀 ROAS > 2.0 avant de scale",
                    "Fréquence > 2.5 en 7j : nouvelle créa urgente",
                ],
            },
            {
                "title": "Formats natifs gagnants", "color": "cyan", "icon": "🎬",
                "items": [
                    "UGC face caméra : 15–30s, son naturel ambiant",
                    "Spark Ads : boostez vos contenus organiques TikTok",
                    "Trending audio : utilisez les sons tendance dans les 48h",
                    "Text-overlay : sous-titres auto OU manuels stylisés",
                    "Duet / Reaction : réaction au produit en temps réel",
                ],
            },
        ],
        "guides": [
            {"title": "🎬 Créer des hooks qui stoppent le scroll", "body": """**Les 5 types de hooks qui convertissent :**

1. **La question directe** : « Tu sais pourquoi ton ROAS chute chaque mois ? »
2. **Le résultat choquant** : « J'ai fait 12 000€ en 4 jours avec une pub de 300€ »
3. **Le contre-intuitif** : « Stop de cibler tes concurrents sur Meta — voici pourquoi »
4. **L'identification** : « Ce problème concerne TOUS les e-commerçants en 2025 »
5. **Le teaser** : « Je vais te montrer exactement comment j'ai fait... regarde jusqu'à la fin »

**Erreurs communes :**
- Texte overlay trop long (max 6 mots en hook)
- Visage hors cadre ou mal éclairé
- Audio de mauvaise qualité (deal breaker sur TikTok)
- CTA vague (« cliquez ici ») → soyez précis (« Lien en bio — offre 48h »)"""},
            {"title": "⚙️ Setup campagne TikTok Ads (structure 2025)", "body": """**Budget minimum :** 30–50€/jour pour que l'algo apprenne correctement.

**Structure recommandée :**
```
Campagne — [Objectif : Conversions / Achat]
  +-- Adset 1 : Broad (18-35, FR) — pas d'intérêts
  +-- Adset 2 : Custom Audience (visiteurs 30j)
  +-- Adset 3 : Lookalike 1-5% acheteurs
      +-- Créa 1 (UGC 15s)
      +-- Créa 2 (Texte overlay + produit)
      +-- Créa 3 (Témoignage 20s)
```

**Spark Ads vs. non-Spark :**
- Spark Ads (boost d'un post organique) = meilleure crédibilité sociale, commentaires visibles
- Non-Spark = contrôle total, idéal pour tester des angles sans compromettre votre compte organique
- Recommandation : testez les 2 et comparez le CTR

**Pixel TikTok :** Installez le pixel TikTok ET l'API Conversions (server-side) pour contourner les adblockers — impact +15-25% sur les données remontées."""},
            {"title": "🔄 Rythme de testing créatif", "body": """**Règle d'or TikTok :** Les créas se fatiguent 3x plus vite que sur Meta.

**Cycle recommandé :**
- Semaine 1-2 : testez 3-5 créas, budget 30-50€/j par adset
- J3 : regardez le VTR à 6s. < 20% = hook raté, coupez la créa
- J5 : regardez le CTR et le CPA. > objectif = scalez le budget x1.5
- Semaine 3 : créez 2-3 variations des créas gagnantes (même angle, format différent)
- Semaine 4+ : nouvelles créas sur nouveaux angles si le ROAS baisse

**Rotation créative :** 1 nouvelle créa par semaine minimum pour maintenir les performances."""},
        ],
    },
    "google": {
        "label": "Google Ads",
        "cards_heading": "Frameworks rapides", "guides_heading": "Guide complet Google Ads",
        "cards": [
            {
                "title": "Structure d'annonce Search RSA", "color": "google_blue", "icon": "🔍",
                "items": [
                    "Headline 1 (30 car.) : mot clé principal exact",
                    "Headline 2 (30 car.) : bénéfice principal + chiffre",
                    "Headline 3 (30 car.) : CTA ou urgence (« Dès 47€ »)",
                    "Description 1 (90 car.) : USP principale + preuve",
                    "Description 2 (90 car.) : objection principale + garantie",
                ],
            },
            {
                "title": "Extensions indispensables", "color": "google_blue", "icon": "🔧",
                "items": [
                    "Sitelinks : 4 liens vers pages clés (FAQ, Prix, Témoignages...)",
                    "Callouts : USP courtes (« Livraison 24h », « Garantie 30j »)",
                    "Structured snippets : liste de produits/services",
                    "Call extension : numéro visible (B2B++)",
                    "Price extension : vos offres avec prix visible",
                ],
            },
            {
                "title": "Types de correspondance", "color": "google_green", "icon": "🎯",
                "items": [
                    "[Exact] : contrôle maximum, volume faible",
                    "« Expression » : équilibre volume / pertinence",
                    "Large : volume élevé, nécessite liste de mots exclus",
                    "→ Commencez en Exact, élargissez quand CPA OK",
                    "→ Liste de négatifs : mots hors-cible à exclure dès J1",
                ],
            },
            {
                "title": "Quality Score — les 3 piliers", "color": "google_yellow", "icon": "⭐",
                "items": [
                    "1. Pertinence annonce (mot clé dans headline = +QS)",
                    "2. CTR attendu vs concurrents (créa = différenciation)",
                    "3. Expérience landing page (LRS vous aide ici 🚦)",
                    "QS 7-10 : CPC réduit jusqu'à 50% vs. QS < 5",
                    "LP lente (> 3s) = QS pénalisé — optimisez le Core Web Vitals",
                ],
            },
        ],
        "guides": [
            {"title": "🏗️ Structure de compte recommandée", "body": """**Principe SKAG vs. thématique (2025) :**
Les SKAGs (1 mot clé par adset) sont dépassés. Google favorise les RSA et le broad match intelligent.

**Structure thématique recommandée :**
```
Compte
  +-- Campagne Search — [Produit Principal]
  |     +-- Adgroup : mots clés achat ("acheter X", "prix X", "commander X")
  |     +-- Adgroup : mots clés comparaison ("X vs Y", "meilleur X")
  |     +-- Adgroup : mots clés problème ("comment [résoudre problème]")
  |
  +-- Campagne Shopping — [Flux produit optimisé]
  |
  +-- Campagne Retargeting — [RLSA + Display]
```

**Budget testing :** 20€/j minimum par campagne Search pour que l'algo ait assez de données en 7-14 jours."""},
            {"title": "📈 Stratégies d'enchères — quand utiliser quoi", "body": """| Stratégie | Quand l'utiliser |
|-----------|-----------------|
| Maximiser les clics | Lancement, objectif = données |
| Maximiser les conversions | Après 30+ conversions/mois |
| CPA cible | Budget stable + historique conversions fiable |
| ROAS cible | E-com avec valeurs paniers variables |
| CPM cible | Display/YouTube — notoriété uniquement |

**Règle :** Ne changez jamais la stratégie d'enchères les 2 premières semaines. L'algo a besoin de 7-14 jours pour apprendre.

**Performance Max :** Évitez en cold traffic pur — PMax cannibalisera vos campagnes Search. Activez-le une fois que Search fonctionne et que vous avez des données de conversion."""},
            {"title": "🛒 Google Shopping — optimiser son flux", "body": """**Les 3 éléments qui font 80% du succès Shopping :**

1. **Titre produit** (le plus important) :
   - Format : `[Marque] [Type produit] [Attribut principal] [Taille/Couleur/Variante]`
   - Exemple : « Nike Air Max 90 Blanc Homme 42 — Chaussures Running »
   - Le mot clé doit être dans les 70 premiers caractères

2. **Image produit** :
   - Fond blanc ou transparent — pas de lifestyle pour Shopping
   - Produit bien centré, occupe > 75% du cadre
   - PNG haute résolution (min. 800x800)

3. **Prix** :
   - Prix barré (prix_comparaison) très visible améliore le CTR
   - Frais de port clairement affichés (ou « Livraison gratuite »)
   - Promotions Merchant Center = badge « Promotion » sur l'annonce

**Segmentation des enchères :** Créez des groupes de produits séparés pour vos bestsellers (enchère haute) vs. catalogue complet (enchère basse)."""},
        ],
    },
    "funnel": {
        "label": "Funnel Écom",
        "cards_heading": "Structures de funnels", "guides_heading": "Les règles immuables d'une landing page qui convertit",
        "cards": [
            {
                "title": "Funnel Direct Response", "color": "accent", "icon": "🎯",
                "items": [
                    "Ad → Landing Page courte → Checkout",
                    "⚡ Le plus simple, idéal pour tester",
                    "LP : 500-800 mots, 1 CTA, pas de nav",
                    "Checkout : 1-page, confiance++",
                    "Upsell : bump offer sur checkout",
                ],
            },
            {
                "title": "Funnel VSL (Video Sales Letter)", "color": "success", "icon": "🎬",
                "items": [
                    "Ad → LP avec vidéo → Checkout → Upsells",
                    "📹 VSL 8-20 min pour produits 97€+",
                    "Vidéo autoplay sans controls (dès possible)",
                    "CTA apparaît à 60% de la vidéo",
                    "Upsell 1 (complémentaire) + Upsell 2 (premium)",
                ],
            },
            {
                "title": "Funnel Lead Magnet", "color": "warning", "icon": "📧",
                "items": [
                    "Ad → Optin (email) → Email nurturing → Vente",
                    "🎁 Idéal : info-produit, coaching, SaaS",
                    "Lead magnet : valeur perçue élevée, résultat rapide",
                    "Sequence 5 emails : valeur → valeur → pitch → urgence → dernière chance",
                    "Retargeting parallèle sur les optins non-convertis",
                ],
            },
        ],
        "cards2": [
            {
                "title": "Structure LP haute conversion", "color": "accent", "icon": "📄",
                "items": [
                    "① Hero : headline + sous-titre + CTA above the fold",
                    "② Problème : « Vous aussi vous souffrez de... »",
                    "③ Solution : votre produit = le pont",
                    "④ Preuves : before/after, témoignages, chiffres",
                    "⑤ Offre : ce que vous obtenez (offer stack)",
                    "⑥ Garantie : réduction du risque perçu",
                    "⑦ CTA final : urgence + bouton",
                ],
            },
            {
                "title": "Les erreurs qui tuent la conversion", "color": "danger", "icon": "⚠️",
                "items": [
                    "❌ Navigation header visible (fuite = -20-40% CVR)",
                    "❌ CTA générique (« En savoir plus », « Cliquer ici »)",
                    "❌ Prix sans contexte (pas de comparaison / barré)",
                    "❌ Garantie absente ou invisible",
                    "❌ Pas de preuve sociale above the fold",
                    "❌ Page trop lente > 3s (Google = -53% de taux de rebond)",
                ],
            },
            {
                "title": "Offer Stack — comment présenter l'offre", "color": "success", "icon": "🎁",
                "items": [
                    "Listez TOUT ce que le client obtient avec valeur €",
                    "Produit principal : « Valeur : 197€ »",
                    "Bonus 1 : « Valeur : 97€ » (doit sembler plus cher que le prix)",
                    "Bonus 2 : « Valeur : 47€ »",
                    "Garantie 30j : « Risque zéro »",
                    "Prix total barré → « Aujourd'hui seulement : 47€ »",
                ],
            },
            {
                "title": "Optimisation du checkout", "color": "warning", "icon": "🛒",
                "items": [
                    "1-page checkout = meilleur CVR (Shopify, ThriveCart...)",
                    "Bump offer visible (+15-25% revenu moyen)",
                    "Logos de paiement sécurisé sous le bouton",
                    "Résumé commande visible à droite du formulaire",
                    "Testimonial ou stat sous le CTA checkout",
                ],
            },
        ],
        "guides": [
            {"title": "📊 Benchmarks CVR par type de page", "body": """| Type de page | CVR faible | CVR moyen | CVR excellent |
|---|---|---|---|
| Landing page cold traffic | < 1% | 1.5–3% | > 4% |
| Page produit ecom | < 1.5% | 2–4% | > 5% |
| Checkout (visiteurs LP) | < 30% | 40–60% | > 70% |
| Optin page (lead magnet) | < 20% | 30–50% | > 60% |
| Upsell 1 | < 10% | 15–25% | > 35% |

*Ces benchmarks varient selon le prix, la niche et la source de trafic. Utilisez LRS pour identifier ce qui plombe votre CVR.*"""},
        ],
    },
    "copywriting": {
        "label": "Copywriting",
        "cards_heading": "Frameworks de copywriting", "guides_heading": "Templates prêts à l'emploi",
        "cards": [
            {
                "title": "PAS — Problem · Agitate · Solve", "color": "accent", "icon": "🔥",
                "items": [
                    "P : Nommez le problème EXACTEMENT comme le client le ressent",
                    "A : Agitez — « Et ça coûte X€ par mois / détruit votre... »",
                    "S : Présentez votre solution comme l'évidence",
                    "⚡ Idéal pour : primary text, email, VSL intro",
                ],
            },
            {
                "title": "AIDA — Attention · Interest · Desire · Action", "color": "success", "icon": "📈",
                "items": [
                    "A : Attention — hook fort (stat, question, choc)",
                    "I : Interest — pourquoi c'est pertinent POUR EUX",
                    "D : Desire — bénéfices concrets + preuves",
                    "A : Action — CTA clair + urgence",
                    "⚡ Idéal pour : landing page, email séquence",
                ],
            },
            {
                "title": "BAB — Before · After · Bridge", "color": "warning", "icon": "🌉",
                "items": [
                    "Before : « Avant, tu passais 2h à optimiser tes pubs... »",
                    "After : « Imagine avoir le score exact avant de dépenser 1€ »",
                    "Bridge : « C'est exactement ce que fait LRS™ en 15s »",
                    "⚡ Idéal pour : témoignages, ads UGC, email welcome",
                ],
            },
            {
                "title": "Les 4U — Urgent · Unique · Utile · Ultra-spécifique", "color": "cyan", "icon": "✅",
                "items": [
                    "Urgent : pourquoi agir maintenant ? (prix, stock, délai)",
                    "Unique : qu'est-ce que VOUS avez que personne d'autre n'a ?",
                    "Utile : quel résultat concret et mesurable ?",
                    "Ultra-spécifique : « 23% de CVR en 7 jours » > « plus de ventes »",
                    "⚡ Checklist pour chaque headline que vous écrivez",
                ],
            },
            {
                "title": "Formules d'hooks éprouvées", "color": "danger", "icon": "💡",
                "items": [
                    "« [Chiffre] [persona] ont [résultat] en [durée] »",
                    "« La vraie raison pourquoi [problème persiste] »",
                    "« Stop [action commune] — voici ce qui marche vraiment »",
                    "« Comment [résultat désiré] sans [douleur habituelle] »",
                    "« Ce que [autorité] ne veut pas que vous sachiez sur [sujet] »",
                ],
            },
        ],
        "guides": [
            {"title": "📝 Templates primary text Meta Ads (copy-paste)", "body": """**Template PAS (30-60 mots) :**
```
Tu dépenses 500€/mois en pubs Meta et tu te demandes pourquoi ton ROAS plafonne à 1.2?

La vraie raison : ta landing page ne convertit pas le trafic que tu envoies dessus.

[Nom produit] analyse ta LP en 15 secondes et te dit exactement ce qui bloque les conversions.

👉 Teste gratuitement → [Lien]
```

**Template Social Proof (40-70 mots) :**
```
"J'ai passé 3 mois à tester des pubs sans comprendre pourquoi ça ne scalait pas.

LRS m'a dit en 15 secondes que mon hook était à 2/5. J'ai changé la headline.

La semaine suivante : ROAS 3.8 au lieu de 1.4."

— [Prénom], e-commerçant (niche X)

→ Découvrez votre score LRS : [Lien]
```

**Template Direct Response (20-40 mots) :**
```
Votre landing page est prête pour le paid traffic?

Score /20 · Plan d'action · Rewrites générés en 15 secondes.

Utilisé par [X] media buyers en France.

Testez maintenant → [Lien]
```"""},
            {"title": "🎯 Comment écrire une headline qui convertit", "body": """**Les 3 composantes d'une headline parfaite :**

1. **Bénéfice spécifique** (pas une feature) + **timeframe** + **sans douleur**
   - ❌ « Améliorez vos pubs avec notre outil IA »
   - ✅ « Doublez votre ROAS en 7 jours sans changer votre budget pub »

2. **Intégrez un chiffre** — les chiffres spécifiques sont +28% plus mémorisables
   - ❌ « Économisez du temps sur vos audits »
   - ✅ « Auditez votre landing page en 15 secondes chrono »

3. **Adressez le sceptique** — anticipez l'objection #1
   - ❌ « L'outil qui révolutionne le paid traffic »
   - ✅ « Le premier outil d'audit paid traffic qui vous dit exactement QUOI corriger »

**Test rapide :** Si votre headline peut s'appliquer à n'importe quel concurrent, elle est trop générique. Retravaillez-la."""},
            {"title": "⚡ Rédiger un CTA qui convertit", "body": """**Règle : le CTA doit être une continuation logique de la promesse**

| ❌ CTA générique | ✅ CTA spécifique |
|---|---|
| « Acheter maintenant » | « Obtenir mon score /20 → » |
| « En savoir plus » | « Voir comment doubler mon ROAS » |
| « S'inscrire » | « Démarrer mon audit gratuit » |
| « Cliquer ici » | « Analyser ma landing page maintenant » |

**Ajouter de l'urgence crédible :**
- Temps limité : « Offre valable jusqu'au [date proche] »
- Stock limité : « Accès limité à 50 utilisateurs ce mois »
- Bonus expirant : « Bonus offert si vous rejoignez avant minuit »

⚠️ L'urgence inventée détruit la confiance. N'utilisez que ce qui est réel et vérifiable."""},
        ],
    },
}

CHANGELOG_VERSIONS = [
    {"version": "V2.6 — Aujourd'hui", "items": [
        "🆕 Bulk Audit : auditez jusqu'à 20 URLs en 1 clic + import CSV + export résultats CSV",
        "🆕 Monitoring : alertes score (drop/progression ≥2 pts), score trend par page",
        "🆕 Audits planifiés automatiques : surveillance toutes les 7/14/30 jours, exécution au démarrage",
        "🆕 Onboarding interactif : guide de démarrage pour les nouveaux utilisateurs",
        "🆕 Onglet Monitoring avec podium, tableau comparatif et badge d'alerte",
    ]},
    {"version": "V2.5", "items": [
        "🆕 Profils d'audit sauvegardés (charger / sauvegarder vos paramètres habituels)",
        "🆕 Delta de score : progression globale depuis le premier audit visible dans l'Historique",
        "🆕 Tracker d'implémentation des recommandations (checkboxes + barre de progression)",
        "🆕 Bouton Re-audit : URL pré-remplie automatiquement depuis l'Historique",
        "🆕 Projets multi-pages : groupez un funnel complet et auditez tout en 1 clic",
        "🆕 Rapport Client PDF : export branding client avec nom du destinataire",
    ]},
    {"version": "V2.4", "items": [
        "🆕 Export rapport PDF professionnel (branding LRS, fond sombre, 4 pages)",
        "🆕 Mode Comparaison : auditer 2 URLs côte à côte",
        "🆕 Mode Avant/Après : comparer un audit avec un précédent",
        "🆕 Changelog intégré dans l'app",
        "🆕 Benchmark Report 2025 (PDF téléchargeable — valeur €27-47)",
    ]},
    {"version": "V2.3", "items": [
        "🆕 Historique persistant (JSON) — survit au refresh de page",
        "🆕 Warning pages JavaScript / contenu insuffisant",
        "🆕 Jauge visuelle du score (bandeau coloré rouge/orange/vert)",
        "🆕 Few-shot examples dans le prompt — scoring plus cohérent",
        "🆕 Retry automatique OpenAI (3 tentatives avec backoff)",
        "🆕 Détection langue de la page (FR / EN / Mixte)",
    ]},
    {"version": "V2.2", "items": [
        "🔧 Fix détection page produit (/products/ classé en Catalogue → corrigé)",
        "🆕 Scoring adaptatif par type de page (fiche produit ≠ landing page)",
        "🆕 Aperçu du contenu scrapé (debug)",
        "🆕 Priorité above-the-fold dans le scraping",
        "🆕 Graphique d'évolution des scores dans Historique",
        "🔧 User-Agent amélioré pour meilleure compatibilité",
    ]},
    {"version": "V2.1", "items": [
        "🔧 Bug 1 : Scoring trop sévère pour marques établies → sélecteur Marque établie / Nouveau lancement",
        "🔧 Bug 2 : Auto-détection du type de page (Sales, Catalogue, SaaS, Blog, Lead Gen)",
        "🔧 Bug 3 : Recommandations granulaires — Quick Wins, Long Terme, Action Prioritaire #1 avec how_exactly",
        "🆕 max_tokens augmenté à 4500",
    ]},
    {"version": "V2.0 — Version initiale", "items": [
        "✅ Audit Funnel Only / Ads Only / Full Risk",
        "✅ Scoring Hook/Offer/Trust/Friction sur 20",
        "✅ Contexte marché personnalisé",
        "✅ Plan d'action, Rewrite, Ad Creative",
        "✅ Export .txt",
        "✅ Checklist pré-lancement",
        "✅ Historique de session",
        "✅ Gate accès par mot de passe",
        "✅ Deploy Streamlit Cloud",
    ]},
]

BENCHMARK_INTRO = (
    "Scores moyens par niche (Ecom, SaaS, Lead Gen, Coaching…), top 10 erreurs de landing pages, "
    "anatomie d'une page parfaite (18+/20 LRS Score), 6 Quick Wins applicables en moins d'1h, "
    "benchmarks CVR par secteur, top 5 hooks qui convertissent en 2025, roadmap 30 jours pour "
    "passer de 10 à 18/20."
)

BENCHMARK_STATS = [
    {"label": "Score moyen Ecom", "value": "11.2 / 20", "sub": "-1.8 vs SaaS · basé sur 200+ audits LRS"},
    {"label": "Erreur #1", "value": "Hook générique", "sub": "présente dans 78% des pages · fix : promesse spécifique + chiffre"},
    {"label": "Uplift CVR moyen", "value": "+2.1 pts", "sub": "après quick wins · sur pages auditées LRS ≥ 12/20"},
]

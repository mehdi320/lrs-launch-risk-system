# Passation — LRS™ (Launch Risk System)

Document de passation complet, du tout début du projet jusqu'à
maintenant. Sert à réamorcer une nouvelle session Claude sans avoir à
tout réexpliquer. Dernière mise à jour : 2026-09-04, branche
`claude/lrs-creative-generation-testing-akbs8x` (44 commits d'avance
sur `main`).

---

## 1. Objectifs

### Le produit
**LRS™ (Launch Risk System)** combine deux modules pour les vendeurs
ecom et vendeurs de produits digitaux :

1. **Audit pré-lancement** — score une landing page et/ou une pub sur
   20 points (Hook, Offre, Confiance, Friction — /5 chacun), avec une
   méthodologie qui s'adapte au type d'offre (ecommerce/digital) et au
   type de page détecté automatiquement. Rend un verdict net (ne pas
   lancer / tester petit budget / prêt à scaler), un plan d'action
   priorisé, un rewrite complet (headline, bullets, CTA, garantie,
   FAQ), des angles pub et un script UGC. Trois modes : Funnel Only,
   Ads Only, Full Risk (les deux ensemble + détection des
   incohérences pub/page).
2. **Creative Studio** — génération de copy (depuis zéro ou à partir
   d'une référence/swipe), score de structure avant/après, funnel
   builder multi-étapes avec éléments de conversion, test A/B
   statistique avec garde-fous anti faux-positifs et anti-gaspillage
   de budget, séquences email automatiques.

Plus, en support : monitoring (audits planifiés + alertes de score),
bibliothèque personnelle (Ads Library, Swipe Files, Benchmark Report),
export PDF pro / rapports en marque blanche pour les agences,
intégrations (Slack, Sheets, Notion, webhook, API Meta/TikTok Ads).

### Le produit existe sous deux interfaces
- **`app.py`** — l'app Streamlit complète, code historique du projet
  (le plus gros fichier du repo).
- **`pilot_server.py` + `pilot_static/`** — un pilote FastAPI + frontend
  custom (thème clair "glass" façon Apple), construit en parallèle
  pour être la version montrée aux premiers utilisateurs bêta. A
  progressivement rattrapé puis dépassé `app.py` en maturité produit
  (checklist de mise en ligne, sécurité, etc.).

### Grandes phases de travail, dans l'ordre chronologique
1. **Nettoyage et fiabilisation de `app.py`** — audit du code mort,
   correction de bugs réels (scores 0/20 affichés à tort quand le LLM
   renvoyait un JSON illisible ; confusion entre "texte de pub" et
   "page de vente/advertorial" dans le mode A/B Test).
2. **Construction du pilote FastAPI** — d'abord un onglet Audit seul,
   étendu progressivement à la quasi-totalité du périmètre de `app.py`
   (Dashboard, Historique, Suivi, Multi-Audit, Ressources), avec mot de
   passe d'accès, onboarding, monitoring planifié.
3. **Sécurité socle** — rate-limiting sur le login (verrou après 5
   échecs), comparaison à temps constant pour le mot de passe, cookie
   `Secure`, protection SSRF sur toutes les URLs auditées côté serveur.
4. **Refonte visuelle** — nouveau design system sobre (style
   Linear/Stripe/Vercel) puis thème clair "glass" Apple avec sidebar,
   appliqué au pilote ET à `app.py` (sidebar Streamlit 2 niveaux :
   Business Manager / LRS).
5. **Creative Studio complet** — génération de créatifs, A/B testing
   avec garde-fous, séquences email, funnel builder, export PDF,
   serveur MCP dédié exposant 4 outils.
6. **Abonnement payant** — gate Stripe (bundle bêta unique, 50€/mois),
   comptes utilisateurs séparés (`user_accounts.py`), authentification
   par lien magique envoyé par email (pas de mot de passe individuel),
   webhook Stripe (`creative_studio/serving/app.py`), runbook complet
   de configuration (`STRIPE_SMTP_SETUP.md`).
7. **Checklist de mise en ligne du pilote** (les "20 points avant de
   lancer un site", périmètre choisi explicitement par l'utilisateur) :
   robots.txt/sitemap (SEO d'app privée = désindexation volontaire),
   Open Graph, 404 custom, contenu légal (privacy/terms/FAQ),
   accessibilité (aria-label), performance (GZip), titres dynamiques.
8. **Page de vente publique** (`sales-site/`, nouveau projet Next.js) —
   scaffoldée de zéro, avec le vrai copy marketing fourni par
   l'utilisateur (issu d'un Google Doc), en anglais par défaut avec
   bascule vers le français (`/vente` et `/vente/fr`), responsive
   testée sur téléphone/tablette/desktop.
9. **Durcissement sécurité du flux paiement → activation → email** :
   déduplication des webhooks Stripe rejoués (avec relâchement propre
   en cas d'échec de traitement, pour ne jamais perdre un paiement),
   anti-spam sur le renvoi de lien magique, anti-injection d'en-tête
   email.
10. **Pixels publicitaires + consentement cookies** — Meta Pixel et
    Google tag (GA4/Ads) câblés mais inactifs tant qu'aucun ID n'est
    fourni, bandeau de consentement RGPD bilingue qui bloque le
    chargement des scripts tant que le visiteur n'a pas accepté.

## 2. Problématiques

Difficultés réelles rencontrées et comment elles ont été traitées :

- **Faux scores 0/20 affichés à l'utilisateur** — quand le LLM
  renvoyait un JSON malformé/illisible, le code l'affichait quand même
  comme un vrai score au lieu de le traiter comme une erreur. Corrigé
  (commit `3b10886`).
- **Confusion Advertorial vs texte de pub** dans le mode A/B Test — le
  code traitait la page de vente et le texte publicitaire comme
  interchangeables alors que ce sont deux objets d'audit différents.
  Corrigé (commits `570875f`, `1ba81c0`).
- **SSRF possible sur les URLs auditées** — `extract_page()` récupérait
  n'importe quelle URL fournie par l'utilisateur sans filtrage,
  exposant potentiellement le réseau interne du serveur. Bloqué
  (commit `52d75d4`).
- **Brute-force sur le login** — pas de limite de tentatives à
  l'origine. Ajout d'un verrou temporaire après 5 échecs + comparaison
  à temps constant du mot de passe (commit `a773b08`).
- **Peeking statistique et gaspillage de budget** dans les tests A/B de
  Creative Studio — un utilisateur regardant les résultats trop tôt
  pouvait arrêter un test sur un faux signal. Garde-fous ajoutés
  (commit `d8a700d`).
- **Aucun projet Next.js n'existait dans ce repo** avant cette session
  (100% Python) — a nécessité de scaffolder `sales-site/` de zéro
  plutôt que d'ajouter une page dans une structure existante.
- **Sandbox sans accès réseau vers Stripe/SMTP réels.** Cet
  environnement ne peut pas atteindre `api.stripe.com` (CONNECT rejeté
  par la politique réseau) ni un serveur SMTP sur le port 587
  (timeout) — confirmé empiriquement. Conséquence : impossible de
  tester un vrai paiement Stripe ou un vrai envoi d'email depuis cette
  session. Tout a été testé via un webhook non signé
  (`LRS_CS_ALLOW_UNVERIFIED_WEBHOOK=true`) qui simule fidèlement la
  logique métier, sans remplacer un test réel avec `stripe listen` /
  un vrai SMTP.
- **Le copy marketing de la page de vente** est arrivé après une
  première version avec des placeholders `[TEXTE_ICI]` — la page a dû
  être restructurée une seconde fois pour suivre le plan du document
  réellement fourni (Google Doc → PDF), plus riche que le squelette
  générique initial à 5 sections.
- **Régression introduite puis corrigée dans la même session** : la
  protection anti-rejeu ajoutée au webhook Stripe marquait un
  événement comme "traité" *avant* que le travail réel soit terminé.
  Une revue de code a détecté qu'un échec en cours de traitement
  aurait pu faire perdre silencieusement un paiement (compte jamais
  activé, aucun retry ultérieur ne le rattrapant). Corrigé le jour
  même (commit `3a8a14c`), testé avec un scénario de panne reproduit
  fidèlement (payload cassé → 500 → retry avec même event_id → compte
  bien activé).

## 3. Fichiers importants

### Pilote (FastAPI + frontend custom) — le plus abouti des deux
- `pilot_server.py` — backend FastAPI (routes API, login gate, GZip,
  fichiers statiques).
- `pilot_static/index.html` — SPA complète (~140 Ko), toutes les vues :
  Dashboard, Audit, Multi-Audit, Suivi, Historique, Ressources,
  Creative Studio, Intégrations.
- `pilot_static/{privacy,terms,faq,404}.html` — contenu légal/support,
  **gabarits à faire relire par un professionnel** avant mise en ligne
  réelle (marqués comme tels dans chaque page).
- `pilot_static/{robots.txt,sitemap.xml,favicon.svg}` — SEO d'app
  privée (`Disallow: /` volontaire, pas d'indexation).
- `PILOT_UI.md` — doc de référence du pilote.

### App Streamlit historique
- `app.py` — l'app complète (fichier volumineux). `check_access()`
  (mot de passe partagé bêta) puis `check_subscription_access()`
  (abonnement Stripe + lien magique) protègent l'accès.

### Comptes / paiement / email (partagé entre app.py et le webhook)
- `user_accounts.py` — DB SQLite dédiée (`.lrs_users.db`) : tables
  `users`, `magic_links` (tokens à usage unique, 15 min, cooldown
  anti-spam 60s), `processed_stripe_events` (déduplication webhook).
  Fonctions clés : `upsert_user_from_checkout`, `create_magic_link`,
  `consume_magic_link`, `claim_stripe_event` / `release_stripe_event`,
  `is_valid_email`.
- `email_alerts.py` — envoi SMTP (résumé d'audit, alertes de score,
  lien magique), avec protection anti-injection d'en-tête
  (`_is_safe_header_value`).
- `creative_studio/serving/app.py` — service FastAPI séparé hébergeant
  `/webhook/stripe` et `/checkout/beta`.
- `mcp_server/` — serveur MCP exposant 4 outils Creative Studio.
- `test_stripe_webhook.py` — 6 scénarios de test (activation, mise à
  jour statut, résiliation, événement ignoré, rejeu d'event dupliqué,
  échec-puis-retry). Lancer le service avec
  `LRS_CS_ALLOW_UNVERIFIED_WEBHOOK=true uvicorn
  creative_studio.serving.app:app --port 8000` dans un terminal, le
  script dans un autre.
- `test_smtp.py` — test d'envoi SMTP direct.
- `STRIPE_SMTP_SETUP.md` — **runbook à suivre pour la suite** : créer
  le produit Stripe, configurer le webhook (Dashboard), tester en
  local (`stripe listen` + carte de test), configurer SMTP, checklist
  finale des variables d'environnement.

### Page de vente (Next.js, nouveau projet indépendant)
- `sales-site/` — projet Next.js 15.5.25 (App Router + TypeScript +
  Tailwind), son propre `package.json`/`node_modules`/`.next`
  (gitignorés).
- `sales-site/app/vente/page.tsx` — page de vente en **anglais**
  (langue par défaut, `/` redirige ici).
- `sales-site/app/vente/fr/page.tsx` — même page en **français**.
- `sales-site/components/vente-shared.tsx` — constantes de l'offre
  bêta (`SPOTS_TOTAL`, `SPOTS_REMAINING`, `BETA_PRICE`,
  `REGULAR_PRICE` — éditées à la main, aucune logique de countdown) et
  composants UI partagés (`PrimaryCta`, `SectionEyebrow`, `Prose`,
  `CheckList`, `LangSwitch`).
- `sales-site/components/CookieConsent.tsx` — bandeau de consentement
  cookies (bilingue), bloque les pixels tant que non accepté.
- `sales-site/app/layout.tsx` — lit `NEXT_PUBLIC_META_PIXEL_ID` /
  `NEXT_PUBLIC_GTAG_ID`, les passe à `CookieConsent`.
- `sales-site/.env.example` — `NEXT_PUBLIC_STRIPE_LINK` + pixels
  (vides par défaut).

## 4. Ce qui a raté / limites connues

- **Rien n'a pu être testé avec de vrais identifiants Stripe, SMTP,
  Meta Pixel ou Google Ads/Analytics** — le sandbox n'y a pas accès
  réseau, et aucun identifiant réel n'a été fourni. Tout a été testé
  avec des identifiants factices ou en mode webhook non signé. **Rien
  de tout ça n'est donc validé en conditions réelles.**
- **Bug transitoire introduit puis corrigé dans la session** — voir
  section 2. Le code actuel sur la branche est correct et testé contre
  ce scénario précis ; mentionné ici pour que la prochaine session
  sache que ce point a déjà été particulièrement vérifié.
- **Contenu légal non finalisé** — `pilot_static/privacy.html` et
  `terms.html` sont fidèles aux flux de données réels du code, mais
  explicitement marqués "à faire relire par un professionnel"
  (mentions légales de l'exploitant à compléter, avis juridique RGPD à
  obtenir si ciblage UE). Aucune page privacy/terms n'existe encore
  pour `sales-site/`.
- **URLs de domaine encore en placeholder** — `og:url` dans
  `pilot_static/index.html` et le domaine dans `sitemap.xml` utilisent
  un domaine factice (`votre-domaine.example`), à remplacer une fois
  le nom de domaine réel connu.
- **Écart possible dans le copy fourni** — le texte validé (PDF) dit
  "quatre axes... (hook, offre, confiance, friction et cohérence du
  message)", ce qui énumère cinq éléments pour "quatre axes". Reproduit
  tel quel dans les deux versions de la page de vente sans correction,
  n'étant pas en position de modifier un copy déjà validé sans
  confirmation — à vérifier auprès de l'auteur du texte.
- **Pas de social proof** sur la page de vente — décision explicite de
  l'utilisateur ("sera ajouté manuellement plus tard"), donc absent
  par design, pas un oubli.
- **`sales-site/` n'a jamais été déployé** — seulement testé en local
  (`npm run build` + `npm run start`).

## 5. Ce que je compte faire ensuite

Rien n'est en cours — la session s'est arrêtée proprement, tout est
commité et pushé sur `claude/lrs-creative-generation-testing-akbs8x`.
Ce qui reste à faire dépend presque entièrement d'accès (comptes,
réseau) que le sandbox Claude n'a pas :

1. **Configurer Stripe en vrai** — créer le produit/prix, configurer le
   endpoint webhook dans le Dashboard Stripe (`/webhook/stripe`),
   récupérer `STRIPE_WEBHOOK_SECRET`, tester avec `stripe listen` et
   une carte de test avant tout trafic réel. Marche à suivre complète
   dans `STRIPE_SMTP_SETUP.md`.
2. **Configurer un vrai SMTP** — `SMTP_HOST/PORT/USER/PASSWORD`, tester
   avec `test_smtp.py`.
3. **Récupérer le lien de paiement Stripe** et le mettre dans
   `sales-site/.env` (`NEXT_PUBLIC_STRIPE_LINK`) avant de déployer la
   page de vente.
4. **Déployer `sales-site/`** quelque part (Vercel ou autre).
5. **Faire relire le contenu légal** (`privacy.html`, `terms.html` du
   pilote) par un professionnel avant toute mise en ligne publique.
6. **Quand les comptes pub seront prêts** : renseigner
   `NEXT_PUBLIC_META_PIXEL_ID` et/ou `NEXT_PUBLIC_GTAG_ID` — le bandeau
   de consentement et le chargement conditionnel des scripts sont déjà
   en place, rien d'autre à coder à ce moment-là.
7. **Vérifier la coquille "quatre axes / cinq éléments"** (section 4)
   avec l'auteur du copy avant de la corriger.

Aucune tâche technique n'est bloquée en interne — tout ce qui précède
dépend d'accès que seul l'utilisateur peut fournir.

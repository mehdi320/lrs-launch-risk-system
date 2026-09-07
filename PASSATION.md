# Passation — LRS™ (Launch Risk System)

Document de passation complet, du tout début du projet jusqu'à
maintenant. Sert à réamorcer une nouvelle session Claude sans avoir à
tout réexpliquer. Dernière mise à jour : 2026-09-07, branche
`claude/lrs-creative-generation-testing-akbs8x` (49 commits d'avance
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
   incohérences pub/page). **Moteur LLM : Anthropic (Claude)** — voir
   section 10, migré depuis OpenAI.
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
  (le plus gros fichier du repo). C'est la **seule** des deux interfaces
  à avoir aujourd'hui la logique d'abonnement Stripe complète
  (`check_subscription_access()`), donc la seule vers laquelle le lien
  magique envoyé après paiement redirige actuellement (`LRS_APP_URL`).
- **`pilot_server.py` + `pilot_static/`** — un pilote FastAPI + frontend
  custom (thème clair "glass" façon Apple), construit en parallèle
  pour être la version montrée aux premiers utilisateurs bêta. A
  progressivement rattrapé puis dépassé `app.py` en maturité produit
  (checklist de mise en ligne, sécurité, etc.). Depuis cette session,
  il a aussi la **capacité** de gérer le lien magique Stripe
  (`/api/auth/consume-magic-link` etc., voir section 10) mais elle
  n'est **pas branchée** sur son blocage d'accès — décision produit non
  prise : est-ce que le pilote doit devenir l'interface principale à
  laquelle les clients payants accèdent ?

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
11. **Validation Stripe/SMTP en conditions réelles + infra de
    déploiement** (cette session, 2026-09-07) — jusqu'ici tout avait
    été testé avec des identifiants factices (voir ancienne section 4,
    corrigée ci-dessous). Cette fois : Stripe CLI installé et
    authentifié, produit/prix créés dans le sandbox Stripe, paiement
    réel avec carte de test, webhook signé reçu et traité, SMTP Gmail
    réel configuré et testé, lien magique cliqué → app déverrouillée.
    3 bugs bloquants découverts et corrigés (voir section 2). Ajout
    d'un reverse proxy Caddy (TLS Let's Encrypt automatique) au
    déploiement Docker. Port de la logique d'abonnement Stripe dans le
    pilote FastAPI (capacité ajoutée, pas activée). Nettoyage de code
    (audit ruff, dead code). Build de `sales-site/` validé et déployé
    sur Vercel pour test (voir section 4).

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
- **3 bugs bloquants découverts en testant Stripe/SMTP avec de vrais
  identifiants pour la première fois** (2026-09-07) — tous invisibles
  tant qu'on ne teste qu'avec des payloads faits main
  (`LRS_CS_ALLOW_UNVERIFIED_WEBHOOK=true`) :
  - `stripe.api_key` n'était **jamais configuré** nulle part dans le
    code → `/checkout/beta` plantait systématiquement avec une
    `AuthenticationError` dès qu'on l'appelait pour de vrai. Le flux
    funnel historique ne l'avait jamais remarqué car il ne fait que
    rediriger vers un Payment Link statique (aucun appel API Stripe
    côté serveur). Corrigé : `stripe.api_key =
    os.environ.get("STRIPE_SECRET_KEY", "")` ajouté dans
    `creative_studio/serving/app.py`, nouvelle variable
    `STRIPE_SECRET_KEY` documentée dans `.env.example` et
    `STRIPE_SMTP_SETUP.md`.
  - Le webhook appelait `.get()` sur l'objet renvoyé par
    `stripe.Webhook.construct_event()` — un `stripe.Event`
    (StripeObject du SDK), qui supporte l'accès par item
    (`event["type"]`) mais **pas** `.get()`. Résultat : **tout**
    webhook réellement signé échouait en 500, alors que le mode
    `LRS_CS_ALLOW_UNVERIFIED_WEBHOOK` (qui fait `json.loads(payload)`,
    un vrai dict) fonctionnait sans problème — d'où le fait que ça
    n'avait jamais été détecté. Corrigé avec `.to_dict()` (conversion
    récursive, donc `event["data"]["object"]` devient aussi un dict
    exploitable par le code existant sans le réécrire).
  - `LRS_USERS_DB_PATH=""` (vide, pas absente) dans `.env` →
    `user_accounts.DB_PATH` valait `os.environ.get("LRS_USERS_DB_PATH",
    <chemin par défaut>)`, qui ne retombe sur le défaut que si la
    variable est **absente**, pas si elle est **vide**. Avec une
    chaîne vide, `sqlite3.connect("")` ouvre une base SQLite temporaire
    **anonyme, différente à chaque connexion** → `no such table` au
    premier vrai appel. Corrigé avec `os.environ.get("LRS_USERS_DB_PATH")
    or <défaut>` (l'opérateur `or`, pas le 2e argument de `.get()`).
    Recherché dans tout le repo si ce pattern existait ailleurs avec un
    défaut non-trivial (un chemin, typiquement) — un seul cas trouvé,
    corrigé.
- **Déploiement Vercel accidentel en production** (2026-09-07) — la
  CLI Vercel (`vercel --yes` sans `--prod=false`) a déployé
  `sales-site/` directement en production au lieu d'un preview privé,
  rendant le vrai lien de paiement Stripe public avant que le backend
  (VPS) soit prêt à recevoir le webhook. Projet supprimé par précaution
  (`vercel remove`) dès que remarqué. Leçon : toujours forcer un
  déploiement preview explicitement pour un premier essai visuel.

## 3. Fichiers importants

### Pilote (FastAPI + frontend custom) — le plus abouti des deux
- `pilot_server.py` — backend FastAPI (routes API, login gate, GZip,
  fichiers statiques). Depuis cette session : section "Abonnement LRS
  (lien magique Stripe)" avec `/api/auth/consume-magic-link`,
  `/api/auth/subscription-status`, `/api/auth/request-magic-link` —
  même `user_accounts.py` que `app.py`, testé avec un vrai token, mais
  **pas branché** sur `_require_auth` (le blocage d'accès actuel reste
  uniquement le mot de passe partagé).
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
  (abonnement Stripe + lien magique) protègent l'accès. Nettoyée cette
  session (voir section 11) : ~20 variables mortes retirées, dont deux
  vraies fonctionnalités abandonnées en cours de route (un badge de
  delta de score dans l'Historique, une coloration du tableau
  comparatif A/B) — calculées puis jamais branchées sur le rendu,
  supprimées plutôt que complétées (hors périmètre d'un nettoyage).
  Moteur audit : bascule automatique vers **Claude** dès
  qu'`ANTHROPIC_API_KEY` est configurée, sinon OpenAI (comportement
  historique inchangé) — voir `audit_engine.py`.

### Comptes / paiement / email (partagé entre app.py et le webhook)
- `user_accounts.py` — DB SQLite dédiée (`.lrs_users.db`) : tables
  `users`, `magic_links` (tokens à usage unique, 15 min, cooldown
  anti-spam 60s), `processed_stripe_events` (déduplication webhook).
  Fonctions clés : `upsert_user_from_checkout`, `create_magic_link`,
  `consume_magic_link`, `claim_stripe_event` / `release_stripe_event`,
  `is_valid_email`. `DB_PATH` corrigé cette session (voir section 2).
- `email_alerts.py` — envoi SMTP (résumé d'audit, alertes de score,
  lien magique), avec protection anti-injection d'en-tête
  (`_is_safe_header_value`). Testé avec un vrai SMTP Gmail cette
  session (`test_smtp.py`, envoi réel confirmé).
- `creative_studio/serving/app.py` — service FastAPI séparé hébergeant
  `/webhook/stripe` et `/checkout/beta`. `stripe.api_key` et le parsing
  `.to_dict()` corrigés cette session (voir section 2).
- `mcp_server/` — serveur MCP exposant 4 outils Creative Studio.
- `test_stripe_webhook.py` — 6 scénarios de test (activation, mise à
  jour statut, résiliation, événement ignoré, rejeu d'event dupliqué,
  échec-puis-retry). Ré-exécuté cette session après les corrections —
  toujours 6/6 (aucune régression). Lancer le service avec
  `LRS_CS_ALLOW_UNVERIFIED_WEBHOOK=true uvicorn
  creative_studio.serving.app:app --port 8000` dans un terminal, le
  script dans un autre. **Attention** : si `STRIPE_WEBHOOK_SECRET` est
  déjà défini dans `.env`, il prend le pas sur
  `LRS_CS_ALLOW_UNVERIFIED_WEBHOOK` (le code vérifie la signature en
  priorité) — surcharger `STRIPE_WEBHOOK_SECRET=` (vide) sur la ligne
  de commande pour forcer le mode non-vérifié.
- `test_smtp.py` — test d'envoi SMTP direct. Sortie en français avec
  accents : sur Windows/console cp1252, lancer avec
  `PYTHONIOENCODING=utf-8` sinon `UnicodeEncodeError`.
- `STRIPE_SMTP_SETUP.md` — runbook, **suivi et validé de bout en bout**
  cette session en mode Test Stripe (voir section 11). Mis à jour avec
  l'étape `STRIPE_SECRET_KEY` (manquait).

### Déploiement
- `Dockerfile`, `docker-compose.yml` — 3 services (pilote 8600,
  Streamlit 8501, webhook 8000). Depuis cette session : 4e service
  `caddy` (reverse proxy, TLS Let's Encrypt automatique via
  `LRS_DOMAIN`), les 3 services applicatifs liés à `127.0.0.1` sur
  l'hôte (plus exposés directement, seul `caddy` publie 80/443).
- `Caddyfile` — route `app.<LRS_DOMAIN>` → Streamlit,
  `pilot.<LRS_DOMAIN>` → pilote, `api.<LRS_DOMAIN>` → webhook/checkout.
- `DEPLOYMENT.md` — checklist mise à jour (TLS/reverse proxy passé de
  "à faire" à "fait", section dédiée avec les étapes DNS).
- **Jamais testé avec un vrai serveur** (pas de démon Docker
  disponible dans cet environnement) — le VPS cible (Google Cloud Free
  Tier, e2-micro) n'a pas encore été créé, voir section 5.

### Page de vente (Next.js, nouveau projet indépendant)
- `sales-site/` — projet Next.js 15.5.25 (App Router + TypeScript +
  Tailwind), son propre `package.json`/`node_modules`/`.next`
  (gitignorés). Build validé cette session (`npm run build`, OK).
  Déployé une fois sur Vercel pour test (voir section 2, incident
  production) puis retiré — pas de déploiement actif actuellement.
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
- `sales-site/.env.example` — `NEXT_PUBLIC_STRIPE_LINK` (un **Payment
  Link Stripe direct**, indépendant du backend/VPS — le CTA de la page
  de vente ne passe pas par `/checkout/beta`) + pixels (vides par
  défaut).

## 4. Ce qui a raté / limites connues

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
- **`sales-site/` n'est pas déployé actuellement** — testé en local et
  une fois sur Vercel (retiré après un déploiement accidentel en
  production, voir section 2). À redéployer en preview d'abord.
- **Le mot de passe bêta local est un placeholder** —
  `.streamlit/secrets.toml` contient `APP_PASSWORD = "change-moi"`, à
  changer avant toute exposition publique de l'app Streamlit.
- **Écart d'architecture non résolu** — le pilote FastAPI a désormais
  la capacité technique de gérer l'abonnement Stripe (section 11) mais
  ce n'est pas activé, et `LRS_APP_URL` (utilisé dans l'email du lien
  magique) pointe toujours vers Streamlit. Décision produit à prendre :
  le pilote doit-il devenir l'interface principale des clients
  payants ?
- **VPS de production jamais créé** — le déploiement Docker+Caddy est
  prêt côté code mais n'a jamais tourné sur un vrai serveur. L'
  utilisateur a explicitement mis cette étape de côté ("je ferai ça à
  la fin"), ainsi que l'achat du nom de domaine.
- **Stripe Live non configuré** — tout ce qui a été validé cette
  session (section 11) est en mode **Test/sandbox**. Passer en Live
  nécessite : ré-autoriser le CLI Stripe pour le Live (lien de
  ré-autorisation envoyé à l'utilisateur, pas confirmé complété),
  créer un nouveau produit/prix Live, récupérer `sk_live_...`, et
  configurer un vrai endpoint webhook dans le Dashboard Stripe — ce qui
  nécessite lui-même le VPS + domaine ci-dessus (Stripe doit pouvoir
  atteindre l'endpoint publiquement).
- **~70 suggestions de style ruff (bugbear/simplify) volontairement
  ignorées** — gain cosmétique, risque réel non nul (ex. ajouter
  `strict=True` à un `zip()` existant changerait le comportement si des
  listes de longueurs différentes étaient jusqu'ici tolérées). Seul le
  nettoyage à risque nul (imports/variables/f-strings inutilisés,
  catégorie `F` de ruff) a été appliqué.

## 5. Ce que je compte faire ensuite

Rien n'est en cours — la session s'est arrêtée proprement, tout est
commité et pushé sur `claude/lrs-creative-generation-testing-akbs8x`.
Ce qui reste dépend presque entièrement de décisions ou d'accès que
seul l'utilisateur peut fournir :

1. **Finaliser Stripe en Live** — l'utilisateur a un lien de
   ré-autorisation CLI en attente (accès Live). Une fois fait : créer
   le produit/prix Live, récupérer `sk_live_...`, configurer le
   webhook réel dans le Dashboard (nécessite le point 2).
2. **Provisionner l'infra** — l'utilisateur a choisi Google Cloud Free
   Tier (VM `e2-micro`, région `us-west1`/`us-central1`/`us-east1` pour
   rester gratuit) plutôt qu'un VPS payant (Hetzner envisagé un
   temps), et un nom de domaine à acheter — **les deux mis de côté
   explicitement par l'utilisateur pour plus tard**. Une fois prêts :
   déployer `docker compose up -d` (voir `DEPLOYMENT.md`, section TLS),
   pointer le DNS, définir `LRS_DOMAIN`.
3. **Décider de l'architecture d'accès finale** — le pilote a
   maintenant la capacité de lien magique Stripe (section 11) mais
   n'est pas branché dessus. Si le pilote doit devenir l'interface
   principale : brancher `_require_auth` (ou une nouvelle couche) sur
   `/api/auth/subscription-status`, et changer `LRS_APP_URL` pour
   pointer vers le pilote au lieu de Streamlit.
4. **Redéployer `sales-site/` sur Vercel** — en preview d'abord cette
   fois (leçon de l'incident section 2), avant de repasser en
   production une fois le backend prêt à recevoir le webhook.
5. **Changer le mot de passe bêta** (`change-moi`) avant toute
   exposition publique de Streamlit.
6. **Faire relire le contenu légal** (`privacy.html`, `terms.html` du
   pilote, et créer l'équivalent pour `sales-site/`) par un
   professionnel avant toute mise en ligne publique.
7. **Vérifier la coquille "quatre axes / cinq éléments"** (section 4)
   avec l'auteur du copy avant de la corriger.
8. **Quand les comptes pub seront prêts** : renseigner
   `NEXT_PUBLIC_META_PIXEL_ID` et/ou `NEXT_PUBLIC_GTAG_ID` — le bandeau
   de consentement et le chargement conditionnel des scripts sont déjà
   en place, rien d'autre à coder à ce moment-là.
9. **Revue de sécurité complète** — explicitement mise de côté par
   l'utilisateur pour plus tard ("on fera cela plus tard").

Aucune tâche technique n'est bloquée en interne — tout ce qui précède
dépend de décisions produit ou d'accès (comptes, domaine, serveur) que
seul l'utilisateur peut fournir.

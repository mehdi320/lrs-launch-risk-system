# Passation — LRS™ (Launch Risk System)

Document de passation complet, du tout début du projet jusqu'à
maintenant. Sert à réamorcer une nouvelle session Claude sans avoir à
tout réexpliquer. Dernière mise à jour : 2026-09-20, branche `main`
(HEAD `f94c2df` au moment de cette révision).

**Pour le suivi tâche par tâche à court terme (priorités, temps estimé,
répartition Baki/Claude Code), voir `NEXT.md`** — ce document-ci reste la
mémoire longue du projet, `NEXT.md` est le plan d'action courant.

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

### Le produit a une seule interface (depuis le 2026-09-14)
- **`pilot_server.py` + `pilot_static/`** — pilote FastAPI + frontend
  custom (thème clair "glass" façon Apple). C'est **l'unique** interface
  produit : `app.py` (l'ancienne app Streamlit, code historique du
  projet) a été **entièrement retiré** du repo et du déploiement
  (commits `97c28bc`, `2a6f42e`, `392c90d`, 2026-09-14). La décision
  produit "le pilote doit-il devenir l'interface principale ?" évoquée
  dans une version antérieure de ce document est **tranchée** : oui,
  c'est fait.
- Le gate d'accès est réellement branché : `_require_auth`
  (`pilot_server.py:154-169`) accorde l'accès à `/api/*` si la session a
  soit `APP_PASSWORD` (admin/exploitant), soit un `subscriber_email` dont
  l'abonnement Stripe est actif — revérifié en base à **chaque requête**
  (`_active_subscriber_email`, `pilot_server.py:146-151`), pas seulement
  au moment du lien magique. Le lien magique envoyé par email doit donc
  pointer vers l'URL du pilote (`LRS_APP_URL`, port 8600 en local) — ce
  n'était pas le cas par défaut jusqu'à cette révision, voir `NEXT.md`
  tâche 1.
- Chaque abonné a désormais son propre espace de données
  (`data/users/<email>/`, `pilot_server.py:94-127`, commit `97c28bc`) —
  avant ce correctif, deux clients bêta connectés en même temps
  partageaient le même historique, quota et identifiants Ads.

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
12. **Bascule complète vers le pilote + durcissement sécurité**
    (2026-09-11 au 2026-09-14) — la décision produit laissée ouverte en
    section 11 est prise : le pilote FastAPI devient l'unique interface.
    - Sécurité : SSRF, timing attack et brute-force sur mots de passe,
      injection d'en-tête email (`a9e9bda`) ; verrou anti-brute-force
      partagé + messages d'erreur assainis + logging serveur (`00c9160`) ;
      isolation multi-tenant par utilisateur + XSS via sortie LLM
      (`22fbbe8`) ; garde-fou anti-injection de prompt + fix agrégation
      admin multi-comptes (`9c6eecf`) ; race condition sur la
      consommation du lien magique corrigée (`d6721a1`).
    - Abonnement Stripe automatisé de bout en bout : checkout + webhook +
      lien magique, déploiement Docker/Caddy (`3b95983`).
    - Pages légales (privacy/CGU) ajoutées et liées (`85a7b90`,
      `b411a1a`).
    - `app.py`/Streamlit retiré du code, du déploiement et de la doc
      (`97c28bc`, `2a6f42e`, `392c90d`) — voir ci-dessus. Au passage :
      isolation des données par utilisateur dans le pilote, faux plan
      "Free" retiré (il n'existe qu'un seul plan bêta payant).
    - Dépendance `cryptography` manquante de `requirements.txt` ajoutée
      (utilisée pour signer le JWT Google Sheets — ne se voyait qu'en
      installation à froid/Docker, `google-auth` l'installait en
      transitif en local) et `APP_PASSWORD` documenté (`cdab929`).
    - Détection **Advertorial** ajoutée au classifieur de page
      (`detect_page_type()`) — les instructions de scoring dédiées
      existaient déjà mais n'étaient jamais déclenchées (code mort) ; une
      page advertorial était classée à tort Sales Page/SaaS et pénalisée
      pour l'absence d'offre/prix/garantie qui n'a pas vocation à être
      sur ce type de page. Normalisation des accents ajoutée au passage
      pour que les signaux FR matchent le contenu réel (`b7ecf89`).
    - **Mode Funnel 2 étapes** — audite ensemble l'advertorial/page de
      vente ET la page de paiement, avec un rôle de scoring propre à
      chacune (score funnel = 70% le maillon le plus faible + 30% la
      moyenne) plutôt que de les traiter isolément (`cfb4242`, export PDF
      des 2 étapes : `c8a0534`).
    - Exports Sheets/Notion (déjà prêts côté backend) enfin exposés dans
      l'UI à côté du bouton Slack existant (`935d91a`).
    - Budget d'extraction de page relevé de 8000 à 20000 caractères après
      un bug qui pouvait ignorer l'essentiel d'une page longue (`eda5a61`,
      `f94c2df`).

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

### Pilote (FastAPI + frontend custom) — unique interface produit
- `pilot_server.py` (~1580 lignes) — backend FastAPI (routes API, gate
  d'accès, GZip, fichiers statiques, isolation des données par
  utilisateur). Section "Abonnement LRS (lien magique Stripe)" —
  `/api/auth/consume-magic-link`, `/api/auth/subscription-status`,
  `/api/auth/request-magic-link` — **réellement branchée** sur
  `_require_auth` (ligne 154) depuis le 2026-09-14 (commit `97c28bc`) :
  ce n'est plus une capacité inerte, c'est le vrai gate des clients bêta
  (mot de passe partagé réservé à l'exploitant).
- `pilot_static/index.html` — SPA complète, toutes les vues : Dashboard,
  Audit (dont le nouveau mode Funnel 2 étapes), Multi-Audit, Suivi,
  Historique, Ressources, Creative Studio, Intégrations (Slack/Sheets/
  Notion, tous exposés dans l'UI depuis `935d91a`).
- `pilot_static/{privacy,terms,faq,404}.html` — contenu légal/support,
  **toujours marqué "à faire relire par un professionnel"** avant mise
  en ligne réelle — aucun commit de revue légale trouvé après `85a7b90`.
- `pilot_static/{robots.txt,sitemap.xml,favicon.svg}` — SEO d'app
  privée (`Disallow: /` volontaire, pas d'indexation).
- `PILOT_UI.md` — doc de référence du pilote.
- `audit_engine.py` — moteur d'audit. Bascule automatique vers
  **Claude** dès qu'`ANTHROPIC_API_KEY` est configurée, sinon OpenAI.
  Détection de type de page (`detect_page_type()`) : catégorie
  **Advertorial** ajoutée (`b7ecf89`, 2026-09-14) — avant ça une page
  advertorial était classée à tort Sales Page/SaaS. Mode **Funnel 2
  étapes** (`run_funnel_audit()`) audite advertorial/page de vente +
  page de paiement ensemble, score = 70% maillon le plus faible + 30%
  moyenne (`cfb4242`). Budget d'extraction de page : 20000 caractères
  (relevé depuis 8000, `f94c2df`).

### App Streamlit — retirée, n'existe plus
`app.py` a été **supprimé du repo** le 2026-09-14 (commits `97c28bc`,
`2a6f42e`, `392c90d`). Toute mention résiduelle d'`app.py` dans
`STRIPE_SMTP_SETUP.md`/`DEPLOYMENT.md` renvoie au code historique qui a
été **porté** dans `pilot_server.py`, pas à un fichier qui existe
encore. Ne pas chercher `app.py`, `.streamlit/secrets.toml`,
`check_access()`/`check_subscription_access()` dans le repo actuel — ni
`webhook_server.py` (service Stripe autonome de l'ère Streamlit,
lui-même supprimé le 2026-09-20 car mort : non référencé par
`docker-compose.yml` ni `Dockerfile`, remplacé par
`creative_studio/serving/app.py`).

### Comptes / paiement / email
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
  `/webhook/stripe` et `/checkout/beta`. `LRS_APP_URL` par défaut
  corrigé le 2026-09-20 (`http://localhost:8600`, pointait encore vers
  l'ancien port Streamlit 8501).
- `mcp_server/` — serveur MCP exposant 4 outils Creative Studio.
- `test_stripe_webhook.py` — 6 scénarios de test (activation, mise à
  jour statut, résiliation, événement ignoré, rejeu d'event dupliqué,
  échec-puis-retry). Lancer le service avec
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
- `STRIPE_SMTP_SETUP.md` — runbook pas-à-pas, validé de bout en bout en
  mode Test Stripe lors de la session du 2026-09-07.

### Déploiement
- `Dockerfile`, `docker-compose.yml` — **2 services applicatifs**
  (pilote 8600, webhook/checkout Creative Studio 8000 — Streamlit n'en
  fait plus partie) + `caddy` (reverse proxy, TLS Let's Encrypt
  automatique via `LRS_DOMAIN`). Les 2 services applicatifs liés à
  `127.0.0.1` sur l'hôte (pas exposés directement, seul `caddy` publie
  80/443).
- `Caddyfile` — `app.<LRS_DOMAIN>` et `pilot.<LRS_DOMAIN>` → pilote (les
  deux sous-domaines gardés pour compatibilité avec un `LRS_APP_URL`
  déjà distribué), `api.<LRS_DOMAIN>` → webhook/checkout.
- `DEPLOYMENT.md` — checklist à jour.
- **Jamais testé avec un vrai serveur/démon Docker** — le VPS cible
  (Google Cloud Free Tier, e2-micro) n'a toujours pas été créé, voir
  section 5 et `NEXT.md` tâche 7.

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

Résolu depuis la version précédente de ce document, gardé pour mémoire :
l'écart d'architecture (pilote non branché sur Stripe) et le mot de passe
bêta placeholder concernaient tous deux `app.py`/Streamlit, qui n'existe
plus (section 1, section 3). Ce qui reste réellement ouvert :

- **Contenu légal non finalisé** — `pilot_static/privacy.html` et
  `terms.html` sont fidèles aux flux de données réels du code, mais
  explicitement marqués "à faire relire par un professionnel"
  (mentions légales de l'exploitant à compléter, avis juridique RGPD à
  obtenir si ciblage UE). Aucune page privacy/terms n'existe encore
  pour `sales-site/`. Toujours vrai au 2026-09-20.
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
- **`sales-site/` redéployé en preview Vercel le 2026-09-21** (Root
  Directory + Framework Preset corrigés dans le projet Vercel, qui
  pointaient encore sur la config Python héritée de l'ancienne racine du
  repo — build **Ready**, `/vente` vérifié en ligne). Reste en preview,
  pas en production (leçon de l'incident section 2) — la bascule prod se
  fera une fois le backend/VPS prêt à recevoir le webhook Stripe.
- **VPS de production jamais créé** — le déploiement Docker+Caddy est
  prêt côté code (2 services applicatifs + caddy, section 3) mais n'a
  jamais tourné sur un vrai serveur. L'utilisateur a explicitement mis
  cette étape de côté, ainsi que l'achat du nom de domaine.
- **Stripe Live non configuré** — tout ce qui a été validé (session du
  2026-09-07) est en mode **Test/sandbox**. Passer en Live nécessite :
  ré-autoriser le CLI Stripe pour le Live, créer un nouveau produit/prix
  Live, récupérer `sk_live_...`, et configurer un vrai endpoint webhook
  dans le Dashboard Stripe — ce qui nécessite lui-même le VPS + domaine
  ci-dessus (Stripe doit pouvoir atteindre l'endpoint publiquement).
- **Aucun `.env` réel dans le repo** — seul `.env.example` existe (audit
  du 2026-09-20). Impossible de confirmer depuis le code si le
  produit/prix Stripe Test est créé, si le SMTP réel fonctionne, ou la
  valeur réelle d'`APP_PASSWORD` — dépend de la machine/des identifiants
  de l'utilisateur, voir `NEXT.md`.
- **Pas de revue de sécurité formelle et complète** — beaucoup de
  durcissement ponctuel fait (SSRF, brute-force, XSS, injection de
  prompt, isolation multi-tenant, dédup webhook — section 1 phase 12),
  mais aucune passe de revue systématique de bout en bout n'a encore eu
  lieu.
- **~70 suggestions de style ruff (bugbear/simplify) volontairement
  ignorées** — gain cosmétique, risque réel non nul (ex. ajouter
  `strict=True` à un `zip()` existant changerait le comportement si des
  listes de longueurs différentes étaient jusqu'ici tolérées). Seul le
  nettoyage à risque nul (imports/variables/f-strings inutilisés,
  catégorie `F` de ruff) a été appliqué.

## 5. Ce que je compte faire ensuite

**Le suivi tâche par tâche à jour (priorités, temps estimé, répartition
Baki/Claude Code) vit désormais dans `NEXT.md`** — à consulter en premier
pour reprendre le travail. Résumé de ce qui reste, dans l'ordre où
`NEXT.md` le priorise :

1. Remplir un `.env` réel (Stripe Test, SMTP, `APP_PASSWORD`,
   `LRS_APP_URL` pointant vers le pilote) et tester le parcours complet
   paiement → webhook → email → lien magique → accès, maintenant que le
   gate est réellement branché sur le pilote (section 3).
2. Provisionner l'infra — VPS (Google Cloud Free Tier, `e2-micro`) et
   nom de domaine, **mis de côté explicitement par l'utilisateur**.
   Une fois prêts : `docker compose up -d` (voir `DEPLOYMENT.md`),
   pointer le DNS, définir `LRS_DOMAIN`.
3. Finaliser Stripe en Live — ré-autoriser le CLI, créer le produit/prix
   Live, récupérer `sk_live_...`, configurer le webhook réel dans le
   Dashboard (dépend du point 2 : Stripe doit joindre l'endpoint
   publiquement).
4. ~~Redéployer `sales-site/` sur Vercel~~ — fait le 2026-09-21, en
   preview (leçon de l'incident section 2). Reste à repasser en
   production une fois le backend/VPS prêt.
5. Faire relire le contenu légal (`privacy.html`, `terms.html` du
   pilote, et créer l'équivalent pour `sales-site/`) par un
   professionnel avant toute mise en ligne publique.
6. Vérifier la coquille "quatre axes / cinq éléments" (section 4) avec
   l'auteur du copy avant de la corriger.
7. Quand les comptes pub seront prêts : renseigner
   `NEXT_PUBLIC_META_PIXEL_ID` et/ou `NEXT_PUBLIC_GTAG_ID` — le bandeau
   de consentement et le chargement conditionnel des scripts sont déjà
   en place, rien d'autre à coder à ce moment-là.
8. Revue de sécurité systématique de bout en bout — pas encore faite en
   tant que passe dédiée, malgré le durcissement ponctuel déjà réalisé.

Aucune tâche technique n'est bloquée en interne — tout ce qui précède
dépend de décisions produit ou d'accès (comptes, domaine, serveur) que
seul l'utilisateur peut fournir.

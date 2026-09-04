# Passation — LRS™ (Launch Risk System)

Document de passation pour reprendre le projet là où cette session
Claude s'est arrêtée. Dernière mise à jour : 2026-09-04, branche
`claude/lrs-creative-generation-testing-akbs8x`.

---

## 1. Objectifs

Le produit **LRS™ (Launch Risk System)** combine deux modules pour les
vendeurs ecom et vendeurs de produits digitaux :

1. **Audit pré-lancement** — score une landing page et/ou une pub sur
   20 points (Hook/Offre/Confiance/Friction, /5 chacun), rend un
   verdict (ne pas lancer / tester petit budget / prêt à scaler), et
   génère un plan d'action + rewrite + angles pub + script UGC.
2. **Creative Studio** — génération de copy, funnel builder multi-pages,
   test A/B statistique, séquences email, éléments de conversion.

Le produit existe sous **deux interfaces** :
- `app.py` — l'app Streamlit complète, historique du projet.
- `pilot_server.py` + `pilot_static/` — un pilote FastAPI + frontend
  custom (thème clair "glass" façon Apple), plus récent, pensé pour
  être la version montrée aux premiers utilisateurs bêta.

Objectifs de cette session, dans l'ordre où ils ont été traités :

1. Rendre le **pilote** prêt à être montré/déployé : checklist "20
   points avant de lancer un site" (SEO privé, 404, contenu légal,
   accessibilité, performance) — scope limité au pilote, explicitement
   choisi par l'utilisateur (pas `app.py`, pas la future page de vente).
2. Créer la **page de vente publique** (`sales-site/`, Next.js), pensée
   pour être hébergée séparément du pilote, avec le vrai copy marketing
   fourni par l'utilisateur (issu d'un Google Doc), en anglais par
   défaut avec bascule vers le français.
3. **Durcir la sécurité** du flux "paiement Stripe → activation du
   compte → réception du lien de connexion", en amont du jour où le
   vrai webhook Stripe sera branché en production.
4. Réserver la place pour le **tracking publicitaire** (Meta Pixel,
   Google Ads/Analytics) avec un vrai bandeau de consentement cookies,
   pour ne pas avoir à y repenser une fois les identifiants disponibles.

## 2. Problématiques

- **Sandbox sans accès réseau vers Stripe/SMTP réels.** Cet
  environnement ne peut pas atteindre `api.stripe.com` (CONNECT rejeté
  par la politique réseau) ni un serveur SMTP sur le port 587
  (timeout) — confirmé empiriquement, ce n'est pas une question de
  credentials. Conséquence : impossible de tester un vrai paiement
  Stripe de bout en bout, ou un vrai envoi d'email, depuis cette
  session. Tout a été testé via un webhook non signé
  (`LRS_CS_ALLOW_UNVERIFIED_WEBHOOK=true`) qui simule fidèlement la
  logique métier, mais ne remplace pas un test avec `stripe listen` ou
  un vrai SMTP (voir `STRIPE_SMTP_SETUP.md`, section 3).
- **Aucun projet Next.js n'existait dans ce repo** avant cette session
  (100% Python) : il a fallu scaffolder `sales-site/` de zéro
  (package.json, tsconfig, Tailwind, App Router) plutôt que d'ajouter
  une seule page dans une structure existante.
- **Le copy marketing de la page de vente** est arrivé après une
  première version avec des placeholders `[TEXTE_ICI]` — la page a dû
  être restructurée une seconde fois pour suivre le plan du document
  fourni (Google Doc → PDF), plus riche que le squelette générique
  initial à 5 sections.
- **Une régression introduite puis corrigée dans la même session** :
  la protection anti-rejeu ajoutée au webhook Stripe (pour éviter les
  doublons d'activation/email si Stripe retente un événement) marquait
  l'événement comme "traité" *avant* que le travail réel soit terminé.
  Une revue de code a détecté qu'un échec en cours de traitement
  aurait pu faire perdre silencieusement un paiement (compte jamais
  activé, aucun retry ultérieur ne le rattrapant). Corrigé le jour
  même (commit `3a8a14c`) — voir section 4 pour les détails, c'est
  listé ici comme rappel de vigilance plutôt que comme un problème
  encore ouvert.

## 3. Fichiers importants

### Pilote (FastAPI + frontend custom)
- `pilot_server.py` — backend FastAPI du pilote (routes API, login
  gate, GZip, montage des fichiers statiques).
- `pilot_static/index.html` — SPA complète du pilote (~140 Ko,
  toutes les vues : Dashboard, Audit, Multi-Audit, Suivi, Historique,
  Ressources, Creative Studio, Intégrations).
- `pilot_static/{privacy,terms,faq,404}.html` — contenu légal/support,
  gabarits à faire relire par un professionnel avant mise en ligne
  réelle (marqués comme tels dans chaque page).
- `pilot_static/{robots.txt,sitemap.xml,favicon.svg}` — SEO (app
  privée : `Disallow: /` volontaire, pas d'indexation).
- `PILOT_UI.md` — doc de référence du pilote (structure, onglets).

### App Streamlit historique
- `app.py` — l'app complète (très volumineux, ~350k lignes de code au
  total dans le repo Python). Contient `check_access()` (mot de passe
  partagé bêta) et `check_subscription_access()` (abonnement Stripe +
  lien magique), toutes deux avant l'accès aux fonctionnalités.

### Comptes / paiement / email (partagé entre app.py et le webhook)
- `user_accounts.py` — DB SQLite dédiée (`.lrs_users.db`) : table
  `users` (statut d'abonnement), `magic_links` (tokens de connexion à
  usage unique, 15 min), `processed_stripe_events` (déduplication
  webhook). Fonctions clés : `upsert_user_from_checkout`,
  `create_magic_link` (avec cooldown anti-spam 60s),
  `consume_magic_link`, `claim_stripe_event` / `release_stripe_event`,
  `is_valid_email`.
- `email_alerts.py` — envoi SMTP (résumé d'audit, alertes de score,
  lien magique). `_is_safe_header_value()` protège contre l'injection
  d'en-tête SMTP sur tous les envois.
- `creative_studio/serving/app.py` — service FastAPI séparé qui
  héberge `/webhook/stripe` (checkout + cycle de vie abonnement) et
  `/checkout/beta` (création de Session Checkout Stripe).
- `test_stripe_webhook.py` — test d'intégration du webhook (6
  scénarios : activation, mise à jour statut, résiliation, événement
  ignoré, rejeu d'event dupliqué, échec-puis-retry). À lancer avec
  `LRS_CS_ALLOW_UNVERIFIED_WEBHOOK=true uvicorn
  creative_studio.serving.app:app --port 8000` dans un terminal, le
  script dans un autre.
- `test_smtp.py` — test d'envoi SMTP direct.
- `STRIPE_SMTP_SETUP.md` — runbook complet : créer le produit Stripe,
  configurer le webhook (Dashboard), tester en local (`stripe listen`
  + carte de test), configurer SMTP, checklist finale des variables
  d'environnement. **C'est le document à suivre pour la suite.**

### Page de vente (Next.js, nouveau projet)
- `sales-site/` — projet Next.js 15.5.25 (App Router + TypeScript +
  Tailwind), indépendant du reste du repo (son propre
  `package.json`/`node_modules`/`.next`, gitignorés).
- `sales-site/app/vente/page.tsx` — page de vente en **anglais**
  (langue par défaut, `/` redirige ici).
- `sales-site/app/vente/fr/page.tsx` — même page en **français**.
- `sales-site/components/vente-shared.tsx` — constantes de l'offre
  bêta (`SPOTS_TOTAL`, `SPOTS_REMAINING`, `BETA_PRICE`,
  `REGULAR_PRICE` — éditées à la main, aucune logique de countdown) et
  composants UI partagés entre les deux langues (`PrimaryCta`,
  `SectionEyebrow`, `Prose`, `CheckList`, `LangSwitch`).
- `sales-site/components/CookieConsent.tsx` — bandeau de consentement
  cookies (bilingue, détection de langue via l'URL). Bloque le
  chargement des pixels tant que le visiteur n'a pas cliqué
  "Accepter".
- `sales-site/app/layout.tsx` — layout racine, lit
  `NEXT_PUBLIC_META_PIXEL_ID` / `NEXT_PUBLIC_GTAG_ID` et les passe à
  `CookieConsent`.
- `sales-site/.env.example` — toutes les variables : lien Stripe
  (`NEXT_PUBLIC_STRIPE_LINK`), pixels (vides par défaut).

## 4. Ce qui a raté / limites connues

- **Rien n'a pu être testé avec de vrais identifiants Stripe, SMTP,
  Meta Pixel ou Google Ads/Analytics** — le sandbox n'y a pas accès
  réseau, et aucun identifiant réel n'a été fourni. Tout ce qui touche
  à ces services a été testé avec des identifiants factices ou en mode
  webhook non signé. **Rien de tout ça n'est donc validé en conditions
  réelles.**
- **Bug transitoire introduit puis corrigé dans la session elle-même** :
  la première version de la protection anti-rejeu webhook (commit
  `f946286`) marquait un événement Stripe comme traité avant la fin
  réelle du traitement — un paiement aurait pu être perdu (compte
  jamais activé) si le traitement plantait au milieu. Détecté par une
  revue de code demandée par l'utilisateur juste après, corrigé dans la
  foulée (commit `3a8a14c`, testé avec un scénario de panne reproduit
  fidèlement). Le code actuel sur la branche est correct — mentionné
  ici pour que la prochaine session sache que ce point a déjà été
  particulièrement vérifié, et pourquoi.
- **Contenu légal non finalisé** — `pilot_static/privacy.html` et
  `terms.html` sont des gabarits fidèles aux flux de données réels du
  code, mais explicitement marqués "à faire relire par un
  professionnel" (mentions légales de l'exploitant à compléter, avis
  juridique RGPD à obtenir si ciblage UE). Idem, aucune page
  privacy/terms n'existe encore pour `sales-site/`.
- **URLs de domaine encore en placeholder** — `og:url` dans
  `pilot_static/index.html` et le domaine dans `sitemap.xml` utilisent
  un domaine factice (`votre-domaine.example`), à remplacer une fois
  le nom de domaine réel connu.
- **Écart possible dans le copy fourni** — le texte validé (PDF) dit
  "quatre axes... (hook, offre, confiance, friction et cohérence du
  message)", ce qui énumère cinq éléments pour "quatre axes". Reproduit
  tel quel dans `sales-site/app/vente/page.tsx` (et sa version FR) sans
  correction, n'étant pas en position de modifier un copy déjà validé
  sans confirmation — à vérifier auprès de l'auteur du texte.
- **Pas de social proof** sur la page de vente — décision explicite de
  l'utilisateur ("sera ajouté manuellement plus tard"), donc absent par
  design, pas un oubli.

## 5. Ce que je compte faire ensuite

Rien n'est en cours — la session s'est arrêtée proprement, tout est
commité et pushé sur `claude/lrs-creative-generation-testing-akbs8x`.
Voici ce qui reste à faire, **côté utilisateur** pour l'essentiel (accès
réseau/comptes que le sandbox n'a pas), avant de pouvoir relancer une
session Claude dessus :

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
4. **Déployer `sales-site/`** quelque part (Vercel ou autre) — n'a
   jamais été déployé, seulement testé en local (`npm run build` +
   `npm run start`).
5. **Faire relire le contenu légal** (`privacy.html`, `terms.html` du
   pilote) par un professionnel avant toute mise en ligne publique.
6. **Quand les comptes pub seront prêts** : renseigner
   `NEXT_PUBLIC_META_PIXEL_ID` et/ou `NEXT_PUBLIC_GTAG_ID` — le bandeau
   de consentement et le chargement conditionnel des scripts sont déjà
   en place, rien d'autre à coder à ce moment-là.
7. **Vérifier la coquille "quatre axes / cinq éléments"** (section 4)
   avec l'auteur du copy avant de la corriger.

Aucune tâche technique n'est bloquée en interne — tout ce qui précède
dépend d'accès (Stripe, SMTP, comptes pub, hébergement) que seul
l'utilisateur peut fournir.

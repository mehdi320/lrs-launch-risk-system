# Configurer Stripe + SMTP pour l'abonnement bêta LRS

Guide pas-à-pas pour finir de brancher l'abonnement Stripe (gate d'accès à
l'app) mis en place dans le code. Rien ici ne nécessite d'écrire du code —
uniquement des clics dans les dashboards Stripe/SMTP et le remplissage de
`.env`.

Contexte technique (déjà en place, voir DEPLOYMENT.md) :
- `check_subscription_access()` dans `app.py` gate l'accès à l'app.
- Le webhook Stripe est étendu dans `creative_studio/serving/app.py`
  (`POST /webhook/stripe`, port 8000) — même endpoint que les achats
  funnel Creative Studio.
- `GET /checkout/beta` (même fichier) crée la Session Checkout du plan
  bêta et redirige vers Stripe.
- `user_accounts.py` stocke le statut d'abonnement (`.lrs_users.db`) et
  les liens magiques de connexion.
- `test_smtp.py` et `test_stripe_webhook.py` (racine du repo) permettent
  de tester chaque brique séparément avant de tout brancher.

---

## 1. Créer le produit et le prix dans Stripe

Commencez en **mode Test** (bascule en haut à droite du Dashboard Stripe)
pour tout valider avant de passer en mode Live.

1. [dashboard.stripe.com](https://dashboard.stripe.com/test/products) →
   **Product catalog** → **Add product**.
2. Nom : `LRS™ — Bêta` (ou ce que vous voulez, visible par le client sur
   la page Stripe Checkout).
3. **Pricing model** : `Recurring` — `Monthly` — `50,00 €`.
4. Enregistrez, puis ouvrez le produit créé : la ligne de prix affiche un
   ID qui commence par `price_...` — **copiez-le**, c'est votre
   `STRIPE_BETA_PRICE_ID`.
5. [Developers → API keys](https://dashboard.stripe.com/test/apikeys) →
   copiez la **Secret key** (`sk_test_...`) — c'est votre
   `STRIPE_SECRET_KEY`. Sans elle, `/checkout/beta` échoue avec une
   `AuthenticationError` (bug découvert et corrigé le 2026-09-07 : le code
   créait une Session Checkout sans jamais avoir configuré `stripe.api_key`
   — voir `creative_studio/serving/app.py`).

## 2. Configurer le webhook

1. [Developers → Webhooks](https://dashboard.stripe.com/test/webhooks)
   → **Add endpoint**.
2. **Endpoint URL** : `https://<votre-domaine-public>/webhook/stripe`
   — c'est le service `creative_studio.serving.app` (port 8000 en
   interne, voir `docker-compose.yml`). Il doit être exposé publiquement
   (reverse proxy/TLS) pour que Stripe puisse l'atteindre — voir la
   checklist de `DEPLOYMENT.md`.
3. **Événements à écouter** — cliquez **Select events** et cochez
   exactement ces trois-là (le webhook ignore proprement tout le reste) :
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
4. Créez l'endpoint, puis ouvrez-le : la section **Signing secret**
   affiche une valeur `whsec_...` (cliquez **Reveal**) — **copiez-la**,
   c'est votre `STRIPE_WEBHOOK_SECRET`.

## 3. Tester en local avant tout déploiement

Le [Stripe CLI](https://docs.stripe.com/stripe-cli) simule de vrais
événements signés sans toucher au webhook de prod.

```bash
stripe login
# Terminal 1 — lance le service de diffusion en local
uvicorn creative_studio.serving.app:app --port 8000
# Terminal 2 — forwarde les événements Stripe vers votre machine
stripe listen --forward-to localhost:8000/webhook/stripe
```

`stripe listen` affiche un `whsec_...` **temporaire, différent de celui
du Dashboard** — utilisez-le dans `.env` (`STRIPE_WEBHOOK_SECRET`)
uniquement pour cette session de test locale.

Pour un test complet et réaliste (recommandé, plutôt que
`stripe trigger` qui ne simule pas un vrai parcours d'abonnement) :
1. Démarrez aussi `streamlit run app.py` et le service de diffusion.
2. Ouvrez `http://localhost:8000/checkout/beta` dans un navigateur — ça
   doit rediriger vers une vraie page Stripe Checkout (si vous avez une
   erreur 503, `STRIPE_BETA_PRICE_ID` ou `LRS_SALES_PAGE_URL` manque dans
   `.env`).
3. Payez avec une carte de test Stripe : `4242 4242 4242 4242`, toute
   date future, tout CVC, email = une adresse que vous pouvez consulter.
4. Le webhook doit recevoir `checkout.session.completed` (visible dans
   le terminal `stripe listen`) et vous devez recevoir l'email avec le
   lien magique (voir section SMTP ci-dessous — sans SMTP configuré,
   l'activation fonctionne mais l'email ne part pas).
5. Cliquez le lien reçu → vous devez arriver sur l'app débloquée.

Pour tester uniquement la logique du webhook (sans navigateur, sans
carte, sans Stripe CLI) :

```bash
LRS_CS_ALLOW_UNVERIFIED_WEBHOOK=true uvicorn creative_studio.serving.app:app --port 8000
# dans un autre terminal :
python3 test_stripe_webhook.py
```

Ce mode désactive la vérification de signature — **jamais** en
production, uniquement pour ce test local isolé.

## 3bis. Ce que le serveur fait déjà pour vous côté sécurité

Tout ce qui suit est déjà en place dans le code (rien à configurer),
mais utile à savoir avant de brancher le vrai webhook Stripe :

- **Signature vérifiée** — `stripe.Webhook.construct_event()` rejette
  (HTTP 400) toute requête qui n'est pas signée avec votre
  `STRIPE_WEBHOOK_SECRET`. Sans ce secret configuré, le endpoint refuse
  tout par défaut (503) sauf opt-in explicite `LRS_CS_ALLOW_UNVERIFIED_WEBHOOK`
  pour le dev local.
- **Rejeu de webhook sans effet de bord** — Stripe retente un événement
  tant qu'il ne reçoit pas un 2xx rapide, et vous pouvez aussi en
  renvoyer un manuellement depuis le Dashboard. Chaque `event.id` n'est
  traité qu'une seule fois (table `processed_stripe_events`) : un même
  paiement ne peut pas réactiver le compte ni renvoyer plusieurs emails
  de lien de connexion.
- **Mais un paiement n'est jamais perdu en cas de panne** — si le
  traitement plante après avoir réclamé l'event (base de données
  indisponible, bug transitoire...), le claim est relâché et le endpoint
  répond 500 : Stripe retente alors ce même `event.id`, qui sera
  retraité normalement plutôt qu'ignoré comme "déjà traité" sans avoir
  jamais activé le compte.
- **Lien magique à usage unique, 15 min** — token de 256 bits
  (`secrets.token_urlsafe(32)`), marqué "utilisé" dès le premier clic
  (rejouer l'URL ne fonctionne pas), et expiré après 15 minutes.
- **Anti-spam sur le renvoi de lien** — le bouton "Recevez votre lien
  de connexion" de l'écran de verrouillage ne peut pas être utilisé pour
  bombarder la boîte mail de quelqu'un d'autre : si un lien valide a
  déjà été émis pour un email il y a moins de 60s, aucun nouveau n'est
  créé ni envoyé (silencieusement, même message affiché dans tous les
  cas pour ne pas laisser deviner si l'email existe).
- **Anti-énumération de comptes** — que l'email existe, soit inactif,
  invalide, ou rate-limité, l'écran affiche toujours le même message
  générique ("si cet email est associé à un abonnement actif...").
- **Emails validés avant tout envoi** — un email mal formé ou contenant
  un retour chariot/saut de ligne (tentative d'injection d'en-têtes
  SMTP, ex. pour ajouter un Bcc caché) est rejeté avant même d'atteindre
  `smtplib`, à la fois côté appelant (`user_accounts.is_valid_email`) et
  en dernier rempart dans `email_alerts.py`.

## 4. SMTP — envoi du lien magique de connexion

Sans SMTP configuré, un utilisateur qui paie est bien activé en base
mais ne reçoit jamais son lien de connexion.

**Option simple pour démarrer (Gmail)** :
1. Activez la validation en 2 étapes sur le compte Gmail à utiliser.
2. Créez un [mot de passe d'application](https://myaccount.google.com/apppasswords).
3. Dans `.env` :
   ```
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=votre-adresse@gmail.com
   SMTP_PASSWORD=<le mot de passe d'application, pas le mot de passe du compte>
   ```

**Pour la prod**, préférez un service transactionnel (SendGrid, Mailgun,
Resend, Postmark...) — meilleure délivrabilité, pas de limite de volume
Gmail. Le principe est identique : `SMTP_HOST`/`SMTP_USER`/
`SMTP_PASSWORD` fournis par le service (souvent `SMTP_USER=apikey` +
une clé API en guise de mot de passe pour SendGrid).

**Testez avant de brancher le reste :**
```bash
pip install -r requirements.txt   # si pas déjà fait (python-dotenv, etc.)
python3 test_smtp.py votre-adresse-de-test@exemple.com
```
Le script se connecte, s'authentifie, et envoie un vrai email — avec un
message d'erreur clair (auth refusée, host/port injoignable...) si
quelque chose cloche, plutôt que de le découvrir après un vrai paiement.

## 5. Checklist finale des variables d'environnement

À renseigner dans `.env` (voir aussi `.env.example` pour le détail de
chaque variable) :

- [ ] `STRIPE_BETA_PRICE_ID` — étape 1
- [ ] `STRIPE_SECRET_KEY` — étape 1.5 (`sk_test_...` puis `sk_live_...` en prod)
- [ ] `STRIPE_WEBHOOK_SECRET` — étape 2 (le vrai, celui du Dashboard —
      pas celui de `stripe listen` une fois passé en prod)
- [ ] `LRS_APP_URL` — URL publique de l'app Streamlit (ex :
      `https://app.votre-domaine.com`)
- [ ] `LRS_SALES_PAGE_URL` — URL de la page de vente statique
- [ ] `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` — étape 4
- [ ] `LRS_USERS_DB_PATH` — laissez vide sauf besoin spécifique (défaut :
      `.lrs_users.db` à la racine)

Une fois tout rempli et testé en local, suivez `DEPLOYMENT.md` pour le
déploiement (les trois services, dont `creative_studio.serving.app` sur
le port 8000, doivent tourner et ce dernier doit être joignable
publiquement pour que Stripe atteigne le webhook).

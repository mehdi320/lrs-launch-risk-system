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

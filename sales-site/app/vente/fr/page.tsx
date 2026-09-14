import type { Metadata } from "next";
import {
  SPOTS_TOTAL,
  SPOTS_REMAINING,
  BETA_PRICE,
  REGULAR_PRICE,
  PrimaryCta,
  SectionEyebrow,
  SectionHeading,
  Prose,
  CheckList,
  LangSwitch,
} from "@/components/vente-shared";

export const metadata: Metadata = {
  title: "LRS™ — Ne lance jamais une campagne sur une page qui n'est pas prête",
  description:
    "LRS audite ta landing page et ta pub avant que tu dépenses un euro de trafic payant, et rend un verdict net : lance, teste petit budget, ou reprends tout.",
};

export default function VentePageFr() {
  return (
    <main className="min-h-screen bg-[#f5f5f7]">
      <LangSwitch href="/vente" label="EN" />

      {/* ============================== HERO ============================== */}
      <section className="relative overflow-hidden px-6 pb-20 pt-16 sm:pb-28 sm:pt-24">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 -z-10"
          style={{
            background:
              "radial-gradient(1200px circle at 15% -10%, rgba(0,122,255,0.14), transparent 55%), radial-gradient(1000px circle at 90% 5%, rgba(175,82,222,0.10), transparent 50%)",
          }}
        />

        <div className="mx-auto max-w-3xl text-center">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-black/10 bg-white/70 px-4 py-1.5 text-sm font-medium text-[#1d1d1f] backdrop-blur">
            <span className="h-2 w-2 rounded-full bg-accent" />
            Bêta limitée — {SPOTS_REMAINING}/{SPOTS_TOTAL} places restantes
          </div>

          <h1 className="text-4xl font-extrabold leading-[1.08] tracking-tight text-[#1d1d1f] sm:text-6xl">
            Ne lance jamais une campagne sur une page qui n&apos;est pas
            prête à convertir
          </h1>

          <p className="mx-auto mt-6 max-w-xl text-lg text-[#6e6e73] sm:text-xl">
            LRS audite ta landing page et ta pub avant que tu dépenses un
            euro de trafic payant, et rend un verdict net : lance, teste
            petit budget, ou reprends tout.
          </p>

          <div className="mt-10 flex flex-col items-center gap-3">
            <PrimaryCta>Rejoindre la bêta →</PrimaryCta>
            <p className="text-sm text-[#86868b]">
              {BETA_PRICE}/mois à vie · {SPOTS_REMAINING} places seulement
            </p>
          </div>
        </div>
      </section>

      {/* ============================ PROBLÈME ============================ */}
      <section className="px-6 py-20 sm:py-28">
        <div className="mx-auto max-w-3xl">
          <SectionEyebrow>Le problème</SectionEyebrow>
          <SectionHeading>
            Le vrai coût d&apos;un lancement, ce n&apos;est pas la pub.
            C&apos;est ce qu&apos;on ne voit pas avant de la lancer
          </SectionHeading>

          <Prose>
            <p>
              Tu connais la séquence. Tu finis une landing page, tu écris
              une pub, tu es convaincu que ça va marcher (parce que tu y as
              mis trois jours, parce que le brief est bon, parce que
              &laquo;&nbsp;ça se sent&nbsp;&raquo;). Tu mets du budget. Et
              deux jours plus tard tu regardes le CPA en te demandant si le
              problème vient du ciblage, de la créa, ou de la page elle
              même.
            </p>
            <p>
              Le problème, la plupart du temps, ce n&apos;est pas le
              trafic. C&apos;est qu&apos;on a lancé une page ou une pub qui
              n&apos;était de toute façon pas prête à convertir, et
              qu&apos;on l&apos;a découvert avec de l&apos;argent déjà
              dépensé plutôt qu&apos;avant.
            </p>
            <p className="font-semibold text-[#1d1d1f]">
              LRS existe pour supprimer cette étape de découverte a
              posteriori.
            </p>
          </Prose>
        </div>
      </section>

      {/* ========================= POSITIONNEMENT ========================= */}
      <section className="bg-white px-6 py-20 sm:py-28">
        <div className="mx-auto max-w-3xl">
          <SectionEyebrow>Ce que c&apos;est</SectionEyebrow>
          <SectionHeading>
            Un filtre de risque avant dépense, pas un outil de création de
            plus
          </SectionHeading>

          <Prose>
            <p>
              LRS™ (Launch Risk System) est un copilote d&apos;audit pré
              lancement pour le paid traffic (Meta, TikTok, Google). Avant
              que tu mettes un euro de budget, il score ta landing page, ta
              pub, et leur cohérence entre elles, puis rend un verdict de
              lancement net : ne lance pas, teste petit budget, ou prêt à
              scaler.
            </p>
            <p>
              Ce n&apos;est pas un outil qui te dit &laquo;&nbsp;c&apos;est
              plutôt bien écrit&nbsp;&raquo;. C&apos;est un système qui te
              dit si tu dépenses ou si tu corriges d&apos;abord.
            </p>
          </Prose>
        </div>
      </section>

      {/* =========================== MOTEUR D'AUDIT ========================= */}
      <section className="px-6 py-20 sm:py-28">
        <div className="mx-auto max-w-3xl">
          <SectionEyebrow>Le moteur d&apos;audit</SectionEyebrow>
          <SectionHeading>Le cœur du produit</SectionHeading>

          <Prose>
            <p>Tu choisis le mode selon ce que tu as en main.</p>
          </Prose>

          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            <div className="rounded-2xl bg-white p-6 shadow-[0_2px_8px_rgba(0,0,0,0.04)]">
              <h3 className="font-bold text-[#1d1d1f]">Funnel Only</h3>
              <p className="mt-2 text-sm leading-relaxed text-[#6e6e73]">
                Pour auditer une landing page seule.
              </p>
            </div>
            <div className="rounded-2xl bg-white p-6 shadow-[0_2px_8px_rgba(0,0,0,0.04)]">
              <h3 className="font-bold text-[#1d1d1f]">Ads Only</h3>
              <p className="mt-2 text-sm leading-relaxed text-[#6e6e73]">
                Pour auditer un script ou un texte de pub seul.
              </p>
            </div>
            <div className="rounded-2xl border border-accent/30 bg-white p-6 shadow-[0_2px_8px_rgba(0,0,0,0.04)]">
              <h3 className="font-bold text-[#1d1d1f]">Full Risk</h3>
              <p className="mt-2 text-sm leading-relaxed text-[#6e6e73]">
                Le mode le plus complet : audite la pub et la landing
                ensemble et détecte les mismatches entre les deux (la
                promesse de la pub que la page ne tient pas, le ton qui
                change, l&apos;offre qui ne correspond plus).
              </p>
            </div>
          </div>

          <Prose>
            <p>
              Le scoring est structuré sur quatre axes noté sur 20 (hook,
              offre, confiance, friction et cohérence du message), avec une
              méthodologie explicite qui s&apos;adapte au type d&apos;offre
              (ecommerce ou digital) et au type de page détecté
              automatiquement (fiche produit, catalogue, homepage, SaaS,
              lead gen, blog). Ce n&apos;est pas un avis vague sur ta page.
              C&apos;est un score reproductible.
            </p>
          </Prose>

          <div className="mt-6 rounded-2xl border-l-4 border-accent bg-white p-6 text-base font-medium leading-relaxed text-[#1d1d1f] shadow-[0_2px_8px_rgba(0,0,0,0.04)]">
            En deux minutes, tu sais si tu dois lancer, tester avec un
            petit budget, ou tout reprendre, au lieu de le découvrir après
            avoir brûlé 500€ de pub à essayer de le comprendre.
          </div>

          <CheckList
            items={[
              "Un verdict de lancement clair",
              "Un plan d'action priorisé par effort et par impact",
              "Une estimation du CVR actuel comparé au CVR post correction",
              "Un rewrite complet : headline, bullets, CTA, stack d'offre, garantie, FAQ",
              "Des variantes de pub prêtes à l'emploi : angles, hooks, script UGC 20-30s",
              "Détection automatique de la langue (français, anglais, mixte)",
              "Scoring adapté : marque déjà installée ou nouveau lancement",
              "Analyse en streaming avec progression affichée en temps réel",
              "Quick Audit pour un premier avis rapide avant d'aller plus loin",
            ]}
          />
        </div>
      </section>

      {/* ============================ CREATIVE STUDIO ============================ */}
      <section className="bg-white px-6 py-20 sm:py-28">
        <div className="mx-auto max-w-3xl">
          <SectionEyebrow>Creative Studio</SectionEyebrow>
          <SectionHeading>
            Une fois le diagnostic posé, tu corriges dans le même outil
          </SectionHeading>

          <Prose>
            <p>
              Un audit qui te dit ce qui cloche, c&apos;est utile. Un audit
              qui te donne directement le correctif testable, c&apos;est ce
              qui te fait gagner les jours que tu aurais passés à chercher
              un copywriter ou à ouvrir un troisième outil.
            </p>
            <p>
              Creative Studio génère des variantes de copy, depuis zéro ou
              à partir d&apos;une référence existante (le swipe d&apos;un
              concurrent, une page qui a déjà marché pour toi). Il score la
              copy avant et après sur la clarté de la promesse, la preuve,
              la clarté de la cible, les éléments de conversion, la
              lisibilité et la clarté du CTA — un score de structure, pas
              une prédiction de conversion, parce qu&apos;on ne te vendra
              jamais un chiffre qu&apos;on ne peut pas tenir.
            </p>
          </Prose>

          <CheckList
            items={[
              "Génération de copy depuis zéro ou à partir d'une référence (swipe concurrent, page qui a déjà marché)",
              "Score avant/après : promesse, preuve, cible, éléments de conversion, lisibilité, CTA",
              "A/B testing avec garde-fous : arrêt auto des variantes, protection anti-peeking statistique, anti-gaspillage de budget",
              "Funnel Builder multi-étapes, popup exit intent compris",
              "Éléments de conversion intégrés : countdown, réduction limitée dans le temps, compteur de stock",
              "Analytics de drop-off étape par étape",
              "Séquences email générées automatiquement",
              "Export PDF du gagnant d'un test",
              "Création depuis zéro ou optimisation d'une page/pub existante",
            ]}
          />
        </div>
      </section>

      {/* ============================ MONITORING ============================ */}
      <section className="px-6 py-20 sm:py-28">
        <div className="mx-auto max-w-3xl">
          <SectionEyebrow>Dans la durée</SectionEyebrow>
          <SectionHeading>
            Ce n&apos;est pas fait pour un lancement. C&apos;est fait pour
            tous tes lancements
          </SectionHeading>

          <Prose>
            <p>
              Une page qui score bien aujourd&apos;hui ne le fera pas
              forcément dans un mois. LRS planifie des audits automatiques
              (tous les 7, 14 ou 30 jours) et t&apos;alerte dès qu&apos;un
              score bouge de façon significative, à la hausse comme à la
              baisse.
            </p>
          </Prose>

          <CheckList
            items={[
              "Projets multi-pages regroupés et audités en un clic",
              "Connexion API Meta ou TikTok Ads : score LRS relié au ROAS réel de tes campagnes",
              "Audit en masse jusqu'à 20 URLs d'un coup (import et export CSV)",
              "Comparaison de deux pages côte à côte ou avant/après",
              "Audit de la page d'un concurrent avec la même grille que la tienne",
            ]}
          />

          <Prose>
            <p>
              L&apos;historique garde un graphique d&apos;évolution des
              scores et le delta de progression depuis ton tout premier
              audit. LRS ne sert pas qu&apos;au jour du lancement. Il
              devient le tableau de bord qui te dit qu&apos;une page se
              dégrade avant que ton ROAS ne te le dise à ta place.
            </p>
          </Prose>
        </div>
      </section>

      {/* ============================ BIBLIOTHÈQUE ============================ */}
      <section className="bg-white px-6 py-20 sm:py-28">
        <div className="mx-auto max-w-3xl">
          <SectionEyebrow>Une bibliothèque qui grandit avec toi</SectionEyebrow>
          <SectionHeading>
            Pas un outil qu&apos;on rouvre à zéro à chaque fois
          </SectionHeading>

          <CheckList
            items={[
              "Ads Library organisée par plateforme (Meta, TikTok, Google), par type de funnel et par approche de copywriting",
              "Swipe Files privés : tes headlines, hooks et CTA qui ont le mieux scoré, réutilisables d'un audit à l'autre",
              "Détection des patterns qui reviennent dans tes audits réussis",
              "Benchmark Report 2025 et checklist pré-lancement intégrée",
            ]}
          />

          <Prose>
            <p>
              Chaque audit enrichit une bibliothèque personnelle que tu
              réutilises. La valeur s&apos;accumule avec l&apos;usage, elle
              ne repart pas de zéro à chaque lancement.
            </p>
          </Prose>
        </div>
      </section>

      {/* ============================ AGENCES ============================ */}
      <section className="px-6 py-20 sm:py-28">
        <div className="mx-auto max-w-3xl">
          <SectionEyebrow>Pour les agences</SectionEyebrow>
          <SectionHeading>
            Si tu audites pour d&apos;autres comptes que le tien
          </SectionHeading>

          <Prose>
            <p>
              L&apos;export PDF professionnel (branding LRS, quatre pages),
              le Rapport Client personnalisable au nom du destinataire, et
              le Rapport Agency en marque blanche permettent de livrer
              l&apos;audit directement à un client sous ta propre marque,
              sans repasser par un template externe.
            </p>
          </Prose>
        </div>
      </section>

      {/* ============================ INTÉGRATIONS ============================ */}
      <section className="bg-white px-6 py-20 sm:py-28">
        <div className="mx-auto max-w-3xl">
          <SectionEyebrow>Intégrations</SectionEyebrow>
          <SectionHeading>
            LRS s&apos;ajoute à ton workflow, il ne t&apos;en impose pas un
            nouveau
          </SectionHeading>

          <Prose>
            <p>
              Notifications Slack, export Google Sheets et Notion, webhook
              générique, envoi des résultats par email, et connexion API
              directe à Meta Ads et TikTok Ads. Tu n&apos;as pas besoin
              d&apos;aller consulter une app en plus, LRS vient
              s&apos;insérer dans ce que tu utilises déjà.
            </p>
          </Prose>
        </div>
      </section>

      {/* ========================== DIFFÉRENCIATION ========================== */}
      <section className="px-6 py-20 sm:py-28">
        <div className="mx-auto max-w-3xl">
          <SectionEyebrow>La différence</SectionEyebrow>
          <SectionHeading>Ce qui rend LRS différent</SectionHeading>

          <Prose>
            <p>
              La plupart des outils qui existent notent une page. Ils
              s&apos;arrêtent là. LRS rend un verdict de lancement
              actionnable (lancer, tester petit, ne pas lancer), avec le
              correctif déjà généré grâce à Creative Studio, et un suivi
              dans la durée grâce au monitoring, à l&apos;historique et à
              la connexion aux campagnes live. Peu d&apos;outils vont
              jusqu&apos;au verdict, au fix, et au suivi post lancement
              dans un seul et même endroit.
            </p>
          </Prose>
        </div>
      </section>

      {/* ============================ POUR QUI ============================ */}
      <section className="bg-white px-6 py-20 sm:py-28">
        <div className="mx-auto max-w-4xl">
          <div className="text-center">
            <SectionEyebrow>Pour qui</SectionEyebrow>
            <SectionHeading>Fait pour ceux qui lancent souvent</SectionHeading>
          </div>

          <div className="mt-14 grid gap-6 sm:grid-cols-3">
            <div className="rounded-3xl border border-black/5 bg-[#f5f5f7] p-8">
              <div className="mb-4 text-3xl">📈</div>
              <h3 className="mb-2 text-base font-bold text-[#1d1d1f]">
                Media buyers &amp; marketeurs paid traffic
              </h3>
              <p className="text-sm leading-relaxed text-[#6e6e73]">
                Meta, TikTok, Google Ads — pour ceux qui lancent des
                campagnes régulièrement et n&apos;ont pas le temps de
                découvrir après coup qu&apos;une page n&apos;était pas
                prête.
              </p>
            </div>
            <div className="rounded-3xl border border-black/5 bg-[#f5f5f7] p-8">
              <div className="mb-4 text-3xl">🛒</div>
              <h3 className="mb-2 text-base font-bold text-[#1d1d1f]">
                E-commerçants &amp; lanceurs de produits digitaux
              </h3>
              <p className="text-sm leading-relaxed text-[#6e6e73]">
                Formations, SaaS — avant de mettre du budget en place.
              </p>
            </div>
            <div className="rounded-3xl border border-black/5 bg-[#f5f5f7] p-8">
              <div className="mb-4 text-3xl">🏢</div>
              <h3 className="mb-2 text-base font-bold text-[#1d1d1f]">
                Agences paid traffic
              </h3>
              <p className="text-sm leading-relaxed text-[#6e6e73]">
                Pour celles qui auditent des comptes clients et doivent
                livrer un rapport professionnel sous leur propre marque.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ============================ OFFRE BÊTA ============================ */}
      <section className="px-6 py-20 sm:py-28">
        <div className="mx-auto max-w-2xl">
          <div className="text-center">
            <SectionEyebrow>Offre de lancement</SectionEyebrow>
            <SectionHeading>
              L&apos;accès complet, au tarif de la bêta
            </SectionHeading>
            <p className="mx-auto mt-4 max-w-xl text-lg text-[#6e6e73]">
              Un seul plan, tout inclus. Le tarif reste bloqué à vie tant
              que ton abonnement est actif.
            </p>
          </div>

          <div className="mt-12 overflow-hidden rounded-[32px] border border-black/5 bg-white shadow-[0_20px_60px_rgba(0,0,0,0.08)]">
            <div className="bg-[#1d1d1f] px-8 py-4 text-center text-sm font-semibold text-white">
              {SPOTS_REMAINING} places sur {SPOTS_TOTAL} disponibles
            </div>

            <div className="p-8 sm:p-10">
              <div className="text-center">
                <p className="text-sm font-semibold uppercase tracking-wide text-[#86868b]">
                  Accès complet — Audit + Creative Studio
                </p>
                <div className="mt-3 flex items-end justify-center gap-2">
                  <span className="text-5xl font-extrabold text-[#1d1d1f]">
                    {BETA_PRICE}
                  </span>
                  <span className="pb-1.5 text-lg text-[#6e6e73]">/mois</span>
                </div>
                <p className="mt-2 text-sm text-[#6e6e73]">
                  Prix bloqué à vie · réservé aux {SPOTS_TOTAL} premiers
                  inscrits
                  <br />
                  <span className="line-through">
                    {REGULAR_PRICE}/mois
                  </span>{" "}
                  après la bêta
                </p>
              </div>

              <ul className="mt-8 space-y-3 text-sm text-[#1d1d1f]">
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-accent">✓</span>
                  Un seul plan — tout inclus, pas de version limitée
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-accent">✓</span>
                  Audits illimités (Funnel, Ads, Full Risk)
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-accent">✓</span>
                  Creative Studio complet (copy, funnel, tests A/B, emails)
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-accent">✓</span>
                  Tarif figé à vie tant que l&apos;abonnement reste actif
                </li>
              </ul>

              <PrimaryCta className="mt-8 w-full">
                Rejoindre la bêta →
              </PrimaryCta>
              <p className="mt-3 text-center text-xs text-[#86868b]">
                Paiement sécurisé via Stripe · résiliable à tout moment
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ============================ PRÉ-CTA ============================ */}
      <section className="bg-white px-6 py-16 text-center sm:py-20">
        <div className="mx-auto max-w-2xl">
          <SectionHeading>Avant de mettre un euro de plus en pub</SectionHeading>
          <p className="mx-auto mt-4 max-w-xl text-lg text-[#6e6e73]">
            La question n&apos;est pas de savoir si ta prochaine page va
            convertir. C&apos;est de savoir si tu veux le découvrir avant
            ou après avoir payé pour le trafic.
          </p>
        </div>
      </section>

      {/* ============================ CTA FINAL ============================ */}
      <section className="px-6 pb-24 pt-16 sm:pb-32 sm:pt-20">
        <div className="mx-auto max-w-2xl rounded-[32px] bg-[#1d1d1f] px-8 py-16 text-center sm:px-16">
          <h2 className="text-2xl font-extrabold leading-snug tracking-tight text-white sm:text-3xl">
            Audite ta prochaine landing page ou ta prochaine pub avec LRS,
            et sache en deux minutes si tu lances, si tu testes petit, ou
            si tu reprends tout.
          </h2>
          <div className="mt-8">
            <PrimaryCta>Rejoindre la bêta →</PrimaryCta>
          </div>
          <p className="mt-4 text-sm text-white/50">
            {SPOTS_REMAINING} places restantes sur {SPOTS_TOTAL} · {BETA_PRICE}
            /mois à vie
          </p>
        </div>
      </section>
    </main>
  );
}

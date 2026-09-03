import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "LRS™ — Ne lancez plus une pub à l'aveugle",
  description:
    "LRS audite votre landing page et votre publicité avant que vous ne dépensiez en pub, puis génère le copy et le funnel pour scaler.",
};

// ---------------------------------------------------------------------------
// Champs éditables à la main pour la bêta — volontairement PAS de logique
// (pas de countdown, pas de décrément automatique). Si une place est prise,
// modifiez SPOTS_REMAINING vous-même avant de redéployer.
// ---------------------------------------------------------------------------
const SPOTS_TOTAL = 17;
const SPOTS_REMAINING = 17;
const BETA_PRICE = "50€";
const REGULAR_PRICE = "100€+";

const STRIPE_LINK =
  process.env.NEXT_PUBLIC_STRIPE_LINK && process.env.NEXT_PUBLIC_STRIPE_LINK.length > 0
    ? process.env.NEXT_PUBLIC_STRIPE_LINK
    : "#";

function PrimaryCta({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <a
      href={STRIPE_LINK}
      className={
        "inline-flex items-center justify-center rounded-full bg-accent px-8 py-4 text-base font-semibold text-white shadow-[0_8px_24px_rgba(0,122,255,0.35)] transition hover:bg-[#0066d6] active:scale-[0.98] " +
        className
      }
    >
      {children}
    </a>
  );
}

function SectionEyebrow({ children }: { children: React.ReactNode }) {
  return (
    <p className="mb-3 text-xs font-bold uppercase tracking-[0.14em] text-accent">
      {children}
    </p>
  );
}

export default function VentePage() {
  return (
    <main className="min-h-screen bg-[#f5f5f7]">
      {/* ============================== HERO ============================== */}
      <section className="relative overflow-hidden px-6 pb-20 pt-16 sm:pb-28 sm:pt-24">
        {/* fond dégradé doux, cohérent avec l'identité LRS */}
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
            [TEXTE_ICI — headline principale]
          </h1>

          <p className="mx-auto mt-6 max-w-xl text-lg text-[#6e6e73] sm:text-xl">
            [TEXTE_ICI — sous-headline : promesse en une phrase]
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
        <div className="mx-auto max-w-4xl">
          <div className="text-center">
            <SectionEyebrow>Le problème</SectionEyebrow>
            <h2 className="text-3xl font-extrabold tracking-tight text-[#1d1d1f] sm:text-4xl">
              [TEXTE_ICI — titre section problème : pourquoi les lancements
              ads échouent]
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-lg text-[#6e6e73]">
              [TEXTE_ICI — paragraphe d'intro sur le coût des lancements à
              l'aveugle]
            </p>
          </div>

          <div className="mt-14 grid gap-6 sm:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="rounded-3xl border border-black/5 bg-white p-8 shadow-[0_2px_8px_rgba(0,0,0,0.04)]"
              >
                <div className="mb-4 text-3xl">⚠️</div>
                <h3 className="mb-2 text-lg font-bold text-[#1d1d1f]">
                  [TEXTE_ICI — pain point {i}]
                </h3>
                <p className="text-sm leading-relaxed text-[#6e6e73]">
                  [TEXTE_ICI — développement du pain point {i}]
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============================ SOLUTION ============================ */}
      <section className="bg-white px-6 py-20 sm:py-28">
        <div className="mx-auto max-w-5xl">
          <div className="text-center">
            <SectionEyebrow>La solution</SectionEyebrow>
            <h2 className="text-3xl font-extrabold tracking-tight text-[#1d1d1f] sm:text-4xl">
              [TEXTE_ICI — titre section solution]
            </h2>
            <p className="mx-auto mt-4 max-w-2xl text-lg text-[#6e6e73]">
              [TEXTE_ICI — chapeau présentant les deux modules ensemble]
            </p>
          </div>

          <div className="mt-16 grid gap-8 lg:grid-cols-2">
            {/* Module 1 — Audit */}
            <div className="rounded-3xl border border-black/5 bg-[#f5f5f7] p-8 sm:p-10">
              <div className="mb-5 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-accent/10 text-2xl">
                🚦
              </div>
              <h3 className="text-xl font-bold text-[#1d1d1f]">
                Module 1 — Audit avant lancement
              </h3>
              <p className="mt-3 text-sm leading-relaxed text-[#6e6e73]">
                [TEXTE_ICI — description bénéfice du module Audit]
              </p>

              <ul className="mt-6 space-y-3 text-sm text-[#1d1d1f]">
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-accent">✓</span>
                  Score sur 20 points — Hook, Offre, Confiance, Friction
                  (/5 chacun)
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-accent">✓</span>
                  Réécriture headline, CTA et bullets prêtes à l'emploi
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-accent">✓</span>
                  Angles publicitaires et hooks par plateforme
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-accent">✓</span>
                  Script UGC 20 secondes généré automatiquement
                </li>
              </ul>
            </div>

            {/* Module 2 — Creative Studio */}
            <div className="rounded-3xl border border-black/5 bg-[#f5f5f7] p-8 sm:p-10">
              <div className="mb-5 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-accent/10 text-2xl">
                🎨
              </div>
              <h3 className="text-xl font-bold text-[#1d1d1f]">
                Module 2 — Creative Studio
              </h3>
              <p className="mt-3 text-sm leading-relaxed text-[#6e6e73]">
                [TEXTE_ICI — description bénéfice du module Creative Studio]
              </p>

              <ul className="mt-6 space-y-3 text-sm text-[#1d1d1f]">
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-accent">✓</span>
                  Génération de copy et funnel builder multi-pages
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-accent">✓</span>
                  Test A/B statistique automatisé
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-accent">✓</span>
                  Séquences email prêtes à envoyer
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-accent">✓</span>
                  Éléments de conversion : timer, stock, order bumps,
                  upsell/downsell
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* ============================ OFFRE BÊTA ============================ */}
      <section className="px-6 py-20 sm:py-28">
        <div className="mx-auto max-w-2xl">
          <div className="text-center">
            <SectionEyebrow>Offre de lancement</SectionEyebrow>
            <h2 className="text-3xl font-extrabold tracking-tight text-[#1d1d1f] sm:text-4xl">
              [TEXTE_ICI — titre section offre]
            </h2>
            <p className="mx-auto mt-4 max-w-xl text-lg text-[#6e6e73]">
              [TEXTE_ICI — texte de contextualisation de l'offre bêta]
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
                  Tarif figé à vie tant que l'abonnement reste actif
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

      {/* ============================ CTA FINAL ============================ */}
      <section className="px-6 pb-24 pt-4 sm:pb-32">
        <div className="mx-auto max-w-2xl rounded-[32px] bg-[#1d1d1f] px-8 py-16 text-center sm:px-16">
          <h2 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
            [TEXTE_ICI — titre CTA final]
          </h2>
          <p className="mx-auto mt-4 max-w-md text-lg text-white/70">
            [TEXTE_ICI — dernière phrase d'incitation avant le bouton]
          </p>
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

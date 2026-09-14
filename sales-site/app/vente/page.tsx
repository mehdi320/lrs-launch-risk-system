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
  title: "LRS™ — Never launch a campaign on a page that isn't ready",
  description:
    "LRS audits your landing page and your ad before you spend a dollar on paid traffic, and gives you a clear verdict: launch, test small, or start over.",
};

export default function VentePage() {
  return (
    <main className="min-h-screen bg-[#f5f5f7]">
      <LangSwitch href="/vente/fr" label="FR" />

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
            Beta limited — {SPOTS_REMAINING}/{SPOTS_TOTAL} spots left
          </div>

          <h1 className="text-4xl font-extrabold leading-[1.08] tracking-tight text-[#1d1d1f] sm:text-6xl">
            Never launch a campaign on a page that isn&apos;t ready to
            convert
          </h1>

          <p className="mx-auto mt-6 max-w-xl text-lg text-[#6e6e73] sm:text-xl">
            LRS audits your landing page and your ad before you spend a
            single dollar on paid traffic, and gives you a clear verdict:
            launch, test small, or start over.
          </p>

          <div className="mt-10 flex flex-col items-center gap-3">
            <PrimaryCta>Join the beta →</PrimaryCta>
            <p className="text-sm text-[#86868b]">
              {BETA_PRICE}/mo for life · {SPOTS_REMAINING} spots only
            </p>
          </div>
        </div>
      </section>

      {/* ============================ PROBLEM ============================ */}
      <section className="px-6 py-20 sm:py-28">
        <div className="mx-auto max-w-3xl">
          <SectionEyebrow>The problem</SectionEyebrow>
          <SectionHeading>
            The real cost of a launch isn&apos;t the ad spend. It&apos;s
            what you don&apos;t see before you launch
          </SectionHeading>

          <Prose>
            <p>
              You know the sequence. You finish a landing page, you write
              an ad, you&apos;re convinced it&apos;s going to work (because
              you spent three days on it, because the brief is solid,
              because &laquo;&nbsp;it feels right&nbsp;&raquo;). You turn
              on the budget. Two days later you&apos;re staring at your CPA
              wondering if the problem is targeting, creative, or the page
              itself.
            </p>
            <p>
              Most of the time, the problem isn&apos;t traffic. It&apos;s
              that you launched a page or an ad that wasn&apos;t ready to
              convert in the first place — and you found out with money
              already spent instead of before.
            </p>
            <p className="font-semibold text-[#1d1d1f]">
              LRS exists to remove that after-the-fact discovery step.
            </p>
          </Prose>
        </div>
      </section>

      {/* ========================= POSITIONING ========================= */}
      <section className="bg-white px-6 py-20 sm:py-28">
        <div className="mx-auto max-w-3xl">
          <SectionEyebrow>What it is</SectionEyebrow>
          <SectionHeading>
            A risk filter before you spend, not another creation tool
          </SectionHeading>

          <Prose>
            <p>
              LRS™ (Launch Risk System) is a pre-launch audit copilot for
              paid traffic (Meta, TikTok, Google). Before you commit a
              single dollar of budget, it scores your landing page, your
              ad, and how well they match each other — then gives you a
              clear launch verdict: don&apos;t launch, test with a small
              budget, or ready to scale.
            </p>
            <p>
              It&apos;s not a tool that tells you &laquo;&nbsp;this is
              pretty well written&nbsp;&raquo;. It&apos;s a system that
              tells you whether to spend or fix it first.
            </p>
          </Prose>
        </div>
      </section>

      {/* =========================== AUDIT ENGINE ========================= */}
      <section className="px-6 py-20 sm:py-28">
        <div className="mx-auto max-w-3xl">
          <SectionEyebrow>The audit engine</SectionEyebrow>
          <SectionHeading>The core of the product</SectionHeading>

          <Prose>
            <p>You pick the mode based on what you have.</p>
          </Prose>

          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            <div className="rounded-2xl bg-white p-6 shadow-[0_2px_8px_rgba(0,0,0,0.04)]">
              <h3 className="font-bold text-[#1d1d1f]">Funnel Only</h3>
              <p className="mt-2 text-sm leading-relaxed text-[#6e6e73]">
                To audit a landing page on its own.
              </p>
            </div>
            <div className="rounded-2xl bg-white p-6 shadow-[0_2px_8px_rgba(0,0,0,0.04)]">
              <h3 className="font-bold text-[#1d1d1f]">Ads Only</h3>
              <p className="mt-2 text-sm leading-relaxed text-[#6e6e73]">
                To audit an ad script or ad copy on its own.
              </p>
            </div>
            <div className="rounded-2xl border border-accent/30 bg-white p-6 shadow-[0_2px_8px_rgba(0,0,0,0.04)]">
              <h3 className="font-bold text-[#1d1d1f]">Full Risk</h3>
              <p className="mt-2 text-sm leading-relaxed text-[#6e6e73]">
                The most complete mode: audits the ad and the landing page
                together and catches mismatches between them (a promise
                the ad makes that the page doesn&apos;t back up, a tone
                shift, an offer that no longer matches).
              </p>
            </div>
          </div>

          <Prose>
            <p>
              Scoring is structured across four pillars scored out of 20
              (hook, offer, trust, friction and message consistency), with
              an explicit methodology that adapts to the type of offer
              (ecommerce or digital) and the type of page detected
              automatically (product page, catalog, homepage, SaaS, lead
              gen, blog). This isn&apos;t a vague opinion about your page.
              It&apos;s a reproducible score.
            </p>
          </Prose>

          <div className="mt-6 rounded-2xl border-l-4 border-accent bg-white p-6 text-base font-medium leading-relaxed text-[#1d1d1f] shadow-[0_2px_8px_rgba(0,0,0,0.04)]">
            In two minutes, you know whether to launch, test with a small
            budget, or start over — instead of finding out after burning
            $500 in ad spend trying to figure it out.
          </div>

          <CheckList
            items={[
              "A clear launch verdict",
              "An action plan prioritized by effort and impact",
              "An estimate of your current CVR vs. the CVR after fixes",
              "A complete rewrite: headline, bullets, CTA, offer stack, guarantee, FAQ",
              "Ready-to-use ad variants: angles, hooks, 20-30s UGC script",
              "Automatic language detection (English, French, or mixed)",
              "Scoring adapted to an established brand or a new launch",
              "Streaming analysis with real-time progress",
              "Quick Audit for a fast first read before going deeper",
            ]}
          />
        </div>
      </section>

      {/* ============================ CREATIVE STUDIO ============================ */}
      <section className="bg-white px-6 py-20 sm:py-28">
        <div className="mx-auto max-w-3xl">
          <SectionEyebrow>Creative Studio</SectionEyebrow>
          <SectionHeading>
            Once the diagnosis is made, you fix it in the same tool
          </SectionHeading>

          <Prose>
            <p>
              An audit that tells you what&apos;s wrong is useful. An audit
              that hands you a testable fix directly is what saves you the
              days you&apos;d otherwise spend hunting for a copywriter or
              opening a third tool.
            </p>
            <p>
              Creative Studio generates copy variants, from scratch or
              from an existing reference (a competitor&apos;s swipe, a
              page that already worked for you). It scores the copy before
              and after on promise clarity, proof, audience clarity,
              conversion elements, readability and CTA clarity — a
              structural score, not a conversion prediction, because
              we&apos;ll never sell you a number we can&apos;t back up.
            </p>
          </Prose>

          <CheckList
            items={[
              "Copy generation from scratch or from a reference (competitor swipe, a page that already worked)",
              "Before/after scoring: promise, proof, audience, conversion elements, readability, CTA",
              "A/B testing with guardrails: auto-stop underperforming variants, protection against statistical peeking, protection against wasted test budget",
              "Multi-step Funnel Builder, exit-intent popup included",
              "Built-in conversion elements: countdown, limited-time discount, stock counter",
              "Step-by-step drop-off analytics",
              "Automatically generated email sequences",
              "PDF export of the winning variant",
              "Build from scratch or optimize an existing page/ad",
            ]}
          />
        </div>
      </section>

      {/* ============================ MONITORING ============================ */}
      <section className="px-6 py-20 sm:py-28">
        <div className="mx-auto max-w-3xl">
          <SectionEyebrow>Over time</SectionEyebrow>
          <SectionHeading>
            This isn&apos;t built for one launch. It&apos;s built for all
            your launches
          </SectionHeading>

          <Prose>
            <p>
              A page that scores well today won&apos;t necessarily score
              well in a month. LRS schedules automatic audits (every 7,
              14, or 30 days) and alerts you the moment a score moves
              significantly, up or down.
            </p>
          </Prose>

          <CheckList
            items={[
              "Multi-page projects grouped and audited in one click",
              "Meta or TikTok Ads API connection: LRS score linked to your campaigns' real ROAS",
              "Bulk audit up to 20 URLs at once (CSV import and export)",
              "Side-by-side or before/after comparison of two pages",
              "Audit a competitor's page with the same grid as yours",
            ]}
          />

          <Prose>
            <p>
              History keeps a score evolution chart and your progress
              delta since your very first audit. LRS isn&apos;t just for
              launch day. It becomes the dashboard that tells you a page
              is degrading before your ROAS tells you instead.
            </p>
          </Prose>
        </div>
      </section>

      {/* ============================ LIBRARY ============================ */}
      <section className="bg-white px-6 py-20 sm:py-28">
        <div className="mx-auto max-w-3xl">
          <SectionEyebrow>A library that grows with you</SectionEyebrow>
          <SectionHeading>
            Not a tool you reopen from zero every time
          </SectionHeading>

          <CheckList
            items={[
              "Ads Library organized by platform (Meta, TikTok, Google), funnel type, and copywriting approach",
              "Private Swipe Files: your best-scoring headlines, hooks, and CTAs, reusable from one audit to the next",
              "Detection of recurring patterns across your successful audits",
              "2025 Benchmark Report and a built-in pre-launch checklist",
            ]}
          />

          <Prose>
            <p>
              Every audit enriches a personal library you reuse. Value
              compounds with usage — it doesn&apos;t reset to zero with
              every launch.
            </p>
          </Prose>
        </div>
      </section>

      {/* ============================ AGENCIES ============================ */}
      <section className="px-6 py-20 sm:py-28">
        <div className="mx-auto max-w-3xl">
          <SectionEyebrow>For agencies</SectionEyebrow>
          <SectionHeading>
            If you audit accounts other than your own
          </SectionHeading>

          <Prose>
            <p>
              Professional PDF export (LRS branding, four pages), a
              Client Report customizable with the recipient&apos;s name,
              and a white-label Agency Report let you deliver the audit
              directly to a client under your own brand, without
              switching to an external template.
            </p>
          </Prose>
        </div>
      </section>

      {/* ============================ INTEGRATIONS ============================ */}
      <section className="bg-white px-6 py-20 sm:py-28">
        <div className="mx-auto max-w-3xl">
          <SectionEyebrow>Integrations</SectionEyebrow>
          <SectionHeading>
            LRS fits into your workflow, it doesn&apos;t add a new one
          </SectionHeading>

          <Prose>
            <p>
              Slack notifications, Google Sheets and Notion export, a
              generic webhook, results by email, and a direct API
              connection to Meta Ads and TikTok Ads. You don&apos;t need
              to open one more app — LRS plugs into what you already use.
            </p>
          </Prose>
        </div>
      </section>

      {/* ========================== DIFFERENTIATION ========================== */}
      <section className="px-6 py-20 sm:py-28">
        <div className="mx-auto max-w-3xl">
          <SectionEyebrow>What&apos;s different</SectionEyebrow>
          <SectionHeading>What makes LRS different</SectionHeading>

          <Prose>
            <p>
              Most existing tools score a page. That&apos;s where they
              stop. LRS delivers an actionable launch verdict (launch,
              test small, don&apos;t launch), with the fix already
              generated through Creative Studio, and ongoing tracking
              through monitoring, history, and live campaign connections.
              Few tools go all the way from verdict, to fix, to
              post-launch tracking, in one place.
            </p>
          </Prose>
        </div>
      </section>

      {/* ============================ WHO IT'S FOR ============================ */}
      <section className="bg-white px-6 py-20 sm:py-28">
        <div className="mx-auto max-w-4xl">
          <div className="text-center">
            <SectionEyebrow>Who it&apos;s for</SectionEyebrow>
            <SectionHeading>Built for people who launch often</SectionHeading>
          </div>

          <div className="mt-14 grid gap-6 sm:grid-cols-3">
            <div className="rounded-3xl border border-black/5 bg-[#f5f5f7] p-8">
              <div className="mb-4 text-3xl">📈</div>
              <h3 className="mb-2 text-base font-bold text-[#1d1d1f]">
                Media buyers &amp; paid traffic marketers
              </h3>
              <p className="text-sm leading-relaxed text-[#6e6e73]">
                Meta, TikTok, Google Ads — for people who launch campaigns
                regularly and don&apos;t have time to find out after the
                fact that a page wasn&apos;t ready.
              </p>
            </div>
            <div className="rounded-3xl border border-black/5 bg-[#f5f5f7] p-8">
              <div className="mb-4 text-3xl">🛒</div>
              <h3 className="mb-2 text-base font-bold text-[#1d1d1f]">
                Ecommerce sellers &amp; digital product launchers
              </h3>
              <p className="text-sm leading-relaxed text-[#6e6e73]">
                Courses, SaaS — before committing budget.
              </p>
            </div>
            <div className="rounded-3xl border border-black/5 bg-[#f5f5f7] p-8">
              <div className="mb-4 text-3xl">🏢</div>
              <h3 className="mb-2 text-base font-bold text-[#1d1d1f]">
                Paid traffic agencies
              </h3>
              <p className="text-sm leading-relaxed text-[#6e6e73]">
                For agencies auditing client accounts who need to deliver
                a professional report under their own brand.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ============================ BETA OFFER ============================ */}
      <section className="px-6 py-20 sm:py-28">
        <div className="mx-auto max-w-2xl">
          <div className="text-center">
            <SectionEyebrow>Launch offer</SectionEyebrow>
            <SectionHeading>Full access, at beta pricing</SectionHeading>
            <p className="mx-auto mt-4 max-w-xl text-lg text-[#6e6e73]">
              One plan, everything included. The price stays locked for
              life as long as your subscription stays active.
            </p>
          </div>

          <div className="mt-12 overflow-hidden rounded-[32px] border border-black/5 bg-white shadow-[0_20px_60px_rgba(0,0,0,0.08)]">
            <div className="bg-[#1d1d1f] px-8 py-4 text-center text-sm font-semibold text-white">
              {SPOTS_REMAINING} of {SPOTS_TOTAL} spots available
            </div>

            <div className="p-8 sm:p-10">
              <div className="text-center">
                <p className="text-sm font-semibold uppercase tracking-wide text-[#86868b]">
                  Full access — Audit + Creative Studio
                </p>
                <div className="mt-3 flex items-end justify-center gap-2">
                  <span className="text-5xl font-extrabold text-[#1d1d1f]">
                    {BETA_PRICE}
                  </span>
                  <span className="pb-1.5 text-lg text-[#6e6e73]">/mo</span>
                </div>
                <p className="mt-2 text-sm text-[#6e6e73]">
                  Price locked for life · limited to the first{" "}
                  {SPOTS_TOTAL} sign-ups
                  <br />
                  <span className="line-through">{REGULAR_PRICE}/mo</span>{" "}
                  after the beta
                </p>
              </div>

              <ul className="mt-8 space-y-3 text-sm text-[#1d1d1f]">
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-accent">✓</span>
                  One plan — everything included, no limited tier
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-accent">✓</span>
                  Unlimited audits (Funnel, Ads, Full Risk)
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-accent">✓</span>
                  Full Creative Studio (copy, funnel, A/B tests, emails)
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-0.5 text-accent">✓</span>
                  Price locked for life as long as your subscription stays
                  active
                </li>
              </ul>

              <PrimaryCta className="mt-8 w-full">
                Join the beta →
              </PrimaryCta>
              <p className="mt-3 text-center text-xs text-[#86868b]">
                Secure payment via Stripe · cancel anytime
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ============================ PRE-CTA ============================ */}
      <section className="bg-white px-6 py-16 text-center sm:py-20">
        <div className="mx-auto max-w-2xl">
          <SectionHeading>Before you spend one more dollar on ads</SectionHeading>
          <p className="mx-auto mt-4 max-w-xl text-lg text-[#6e6e73]">
            The question isn&apos;t whether your next page will convert.
            It&apos;s whether you want to find out before or after
            you&apos;ve paid for the traffic.
          </p>
        </div>
      </section>

      {/* ============================ FINAL CTA ============================ */}
      <section className="px-6 pb-24 pt-16 sm:pb-32 sm:pt-20">
        <div className="mx-auto max-w-2xl rounded-[32px] bg-[#1d1d1f] px-8 py-16 text-center sm:px-16">
          <h2 className="text-2xl font-extrabold leading-snug tracking-tight text-white sm:text-3xl">
            Audit your next landing page or ad with LRS, and know in two
            minutes whether to launch, test small, or start over.
          </h2>
          <div className="mt-8">
            <PrimaryCta>Join the beta →</PrimaryCta>
          </div>
          <p className="mt-4 text-sm text-white/50">
            {SPOTS_REMAINING} spots left out of {SPOTS_TOTAL} · {BETA_PRICE}
            /mo for life
          </p>
        </div>
      </section>
    </main>
  );
}

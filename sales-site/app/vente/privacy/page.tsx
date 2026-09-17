import type { Metadata } from "next";
import { LegalLayout, LegalSection } from "@/components/legal-shared";

export const metadata: Metadata = {
  title: "Privacy Policy — LRS™",
  robots: { index: false, follow: false },
};

export default function PrivacyPage() {
  return (
    <LegalLayout
      backHref="/vente"
      backLabel="← Back to LRS™"
      title="Privacy Policy"
      updatedLabel="Last updated: to be filled in before publishing"
      noticeLabel="Template — needs review."
      notice="This text accurately describes the data LRS™ technically
        processes (see the project's code), but it isn't legal advice. Have
        it reviewed by a professional before going live, especially if you
        target users in the EU (GDPR) — operator's legal name, legal basis
        for processing, data protection officer if applicable, etc."
    >
      <LegalSection heading="Who operates LRS™">
        <p>
          [Operator&apos;s legal name], [address or country of
          establishment], [contact email].
        </p>
      </LegalSection>

      <LegalSection heading="Data we process">
        <ul className="list-disc space-y-2 pl-5">
          <li>
            <strong>Content you submit</strong>: landing page URL and/or ad
            copy you paste to run an audit — sent to an AI model (OpenAI or
            Anthropic depending on configuration) to generate the score and
            recommendations.
          </li>
          <li>
            <strong>Email address</strong>: used for authentication
            (single-use login link) and, if you enable it, for sending the
            audit report or monitoring alerts.
          </li>
          <li>
            <strong>Subscription data</strong>: subscription status, Stripe
            customer ID and subscription ID. We never see or store your card
            number — payment is handled entirely by Stripe.
          </li>
          <li>
            <strong>Audit history</strong>: scores and results of the audits
            you run, kept so you can track your progress.
          </li>
          <li>
            <strong>Session cookie</strong>: a single cookie, strictly
            necessary to keep you signed in — no advertising or analytics
            cookie by default.
          </li>
        </ul>
      </LegalSection>

      <LegalSection heading="Recipients / sub-processors">
        <ul className="list-disc space-y-2 pl-5">
          <li>
            <strong>OpenAI and/or Anthropic</strong> — generate the analysis
            from the content you submit.
          </li>
          <li>
            <strong>Stripe</strong> — processes the subscription payment.
          </li>
          <li>
            <strong>Our email (SMTP) provider</strong> — delivers
            transactional emails (login link, reports).
          </li>
          <li>
            If you enable optional integrations (Slack, Google Sheets,
            Notion, Meta/TikTok Ads): those services receive only the data
            you choose to send them.
          </li>
        </ul>
      </LegalSection>

      <LegalSection heading="Retention period">
        <p>
          Your data is kept for as long as your account is active. You can
          request its deletion at any time at [contact email].
        </p>
      </LegalSection>

      <LegalSection heading="Your rights">
        <p>
          Depending on your jurisdiction (GDPR for EU residents in
          particular), you have a right of access, rectification, erasure
          and portability of your data. Contact [contact email] to exercise
          it.
        </p>
      </LegalSection>

      <LegalSection heading="Security">
        <p>
          Passwords and login tokens are handled with constant-time
          comparison, login links are single-use and expire after 15
          minutes, and access to the application is gated by subscription.
        </p>
      </LegalSection>
    </LegalLayout>
  );
}

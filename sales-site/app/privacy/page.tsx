import type { Metadata } from "next";
import { LegalShell, LegalSection, LegalNotice } from "@/components/legal-shared";

// noindex tant que l'identité légale de l'exploitant (raison sociale,
// adresse/pays, email de contact) n'est pas complétée ci-dessous —
// voir LegalNotice. Retirer cette ligne une fois le texte finalisé.
export const metadata: Metadata = {
  title: "Privacy Policy — LRS™",
  robots: { index: false, follow: false },
};

export default function PrivacyPage() {
  return (
    <LegalShell
      backHref="/vente"
      backLabel="← Back to LRS™"
      title="Privacy Policy"
      updatedLabel="Last updated: pending final review before going live"
    >
      <LegalNotice>
        <strong>Draft — operator identity to complete.</strong> This text
        accurately describes what this specific site (the sales page you
        came from, not the LRS app itself) actually does with data,
        based on its source code. It is not legal advice. Before this
        page goes live for real traffic, fill in the operator&apos;s legal
        name and contact email below, and have it reviewed by a
        professional if you are targeting EU visitors (GDPR).
      </LegalNotice>

      <LegalSection heading="Who runs this site">
        <p>
          [Operator legal name / business registration — to complete],
          [address or country of establishment — to complete], [contact
          email — to complete].
        </p>
      </LegalSection>

      <LegalSection heading="What this site does, in plain terms">
        <p>
          This page is a marketing and checkout page for the LRS™
          subscription. It does not collect any audit content, and it
          does not create an account for you — that happens on a
          separate app once you subscribe. There is no contact form and
          no server-side database behind this page.
        </p>
      </LegalSection>

      <LegalSection heading="Data this site processes">
        <ul className="list-disc space-y-2 pl-5">
          <li>
            <strong>Cookie consent choice</strong>: stored only in your
            browser&apos;s local storage, never sent to any server.
          </li>
          <li>
            <strong>Advertising / analytics cookies</strong> (Meta Pixel,
            Google Ads / Analytics): loaded only after you explicitly
            accept the cookie banner. If you decline or ignore it,
            neither script loads and no third-party cookie is set.
          </li>
          <li>
            <strong>Payment information</strong>: when you click to join
            the beta, Stripe collects your email and payment details
            directly — either via a Stripe-hosted checkout or an
            embedded Stripe widget. We never see or store your card
            number; Stripe processes and retains that data under its
            own privacy policy.
          </li>
        </ul>
      </LegalSection>

      <LegalSection heading="Who receives this data">
        <ul className="list-disc space-y-2 pl-5">
          <li>
            <strong>Meta</strong> — only if you accept cookies and the
            Meta Pixel is active.
          </li>
          <li>
            <strong>Google</strong> — only if you accept cookies and
            Google Ads/Analytics is active.
          </li>
          <li>
            <strong>Stripe</strong> — processes your subscription
            payment.
          </li>
        </ul>
      </LegalSection>

      <LegalSection heading="Retention">
        <p>
          Your cookie choice stays in your browser until you clear site
          data or change it via the cookie banner. Stripe retains
          payment and billing data per its own retention policy. This
          site keeps no server-side record of your visit.
        </p>
      </LegalSection>

      <LegalSection heading="Your rights">
        <p>
          If you are in the EU (GDPR) or another jurisdiction with
          similar protections, you have the right to access, correct,
          delete, or export your personal data. For data held by Stripe,
          you can also contact Stripe directly. To exercise these rights
          regarding this site, contact [contact email — to complete].
        </p>
      </LegalSection>

      <LegalSection heading="Related">
        <p>
          See also our{" "}
          <a href="/terms" className="text-accent hover:underline">
            Terms of Service
          </a>
          .
        </p>
      </LegalSection>
    </LegalShell>
  );
}

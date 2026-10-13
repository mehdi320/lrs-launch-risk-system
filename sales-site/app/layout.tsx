import type { Metadata } from "next";
import Script from "next/script";
import { headers } from "next/headers";
import "./globals.css";
import CookieConsent from "@/components/CookieConsent";

export const metadata: Metadata = {
  title: "LRS™ — Launch Risk System",
  description:
    "Audit your landing page and your ad before you spend on paid traffic.",
};

// ---------------------------------------------------------------------------
// Pixels publicitaires (Meta / Google) — emplacement réservé, INACTIF tant
// que les identifiants ne sont pas renseignés dans l'environnement, ET tant
// que le visiteur n'a pas explicitement accepté le bandeau de cookies (voir
// components/CookieConsent.tsx). Rien ne se charge par défaut : pas de
// requête, pas de cookie tiers, pas de faux tracking avec un ID vide.
//
// NEXT_PUBLIC_GTAG_ID accepte indifféremment un ID Google Analytics 4
// ("G-XXXXXXX") ou un ID Google Ads ("AW-XXXXXXX") — même script gtag.js
// des deux côtés, seul le préfixe change.
// ---------------------------------------------------------------------------
const META_PIXEL_ID = process.env.NEXT_PUBLIC_META_PIXEL_ID || "";
const GTAG_ID = process.env.NEXT_PUBLIC_GTAG_ID || "";

// Script du widget Stripe Buy Button — chargé seulement si le bouton est
// réellement configuré (voir components/vente-shared.tsx::PrimaryCta),
// même philosophie que les pixels ci-dessus : rien ne charge par défaut.
const STRIPE_BUY_BUTTON_ID = process.env.NEXT_PUBLIC_STRIPE_BUY_BUTTON_ID || "";

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Nonce posé par middleware.ts (CSP) sur chaque requête — relayé ici aux
  // <Script> que nous contrôlons directement. Les scripts internes générés
  // par Next.js (hydratation RSC) sont, eux, noncés automatiquement par le
  // framework dès qu'il détecte ce nonce dans l'en-tête CSP sortant.
  const nonce = (await headers()).get("x-nonce") || undefined;

  return (
    <html lang="en">
      <body className="font-sans antialiased">
        {children}
        <CookieConsent metaPixelId={META_PIXEL_ID} gtagId={GTAG_ID} nonce={nonce} />
        {STRIPE_BUY_BUTTON_ID && (
          <Script
            src="https://js.stripe.com/v3/buy-button.js"
            strategy="afterInteractive"
            nonce={nonce}
          />
        )}
      </body>
    </html>
  );
}

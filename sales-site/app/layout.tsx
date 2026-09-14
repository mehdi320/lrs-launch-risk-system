import type { Metadata } from "next";
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

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">
        {children}
        <CookieConsent metaPixelId={META_PIXEL_ID} gtagId={GTAG_ID} />
      </body>
    </html>
  );
}

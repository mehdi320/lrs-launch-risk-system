import type { Metadata } from "next";
import Script from "next/script";
import "./globals.css";

export const metadata: Metadata = {
  title: "LRS™ — Launch Risk System",
  description:
    "Audit your landing page and your ad before you spend on paid traffic.",
};

// ---------------------------------------------------------------------------
// Pixels publicitaires (Meta / Google) — emplacement réservé, INACTIF tant
// que les identifiants ne sont pas renseignés dans l'environnement. Rien ne
// se charge par défaut : pas de requête, pas de cookie tiers, pas de faux
// tracking avec un ID vide.
//
// NEXT_PUBLIC_GTAG_ID accepte indifféremment un ID Google Analytics 4
// ("G-XXXXXXX") ou un ID Google Ads ("AW-XXXXXXX") — même script gtag.js
// des deux côtés, seul le préfixe change.
//
// ⚠️ Implication légale à traiter AVANT d'activer un de ces deux ID : le
// pixel Meta et gtag.js posent tous les deux des cookies tiers non
// strictement nécessaires (fbp/fbc, _ga...). Contrairement au pilote LRS
// (un seul cookie de session, exempté RGPD/ePrivacy), la page de vente
// aura alors besoin d'un vrai bandeau de consentement cookies avant
// déclenchement de ces scripts pour les visiteurs UE — pas encore
// implémenté ici, à faire quand vous activez l'un des deux ID.
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

        {GTAG_ID && (
          <>
            <Script
              src={`https://www.googletagmanager.com/gtag/js?id=${GTAG_ID}`}
              strategy="afterInteractive"
            />
            <Script id="gtag-init" strategy="afterInteractive">
              {`
                window.dataLayer = window.dataLayer || [];
                function gtag(){dataLayer.push(arguments);}
                gtag('js', new Date());
                gtag('config', '${GTAG_ID}');
              `}
            </Script>
          </>
        )}

        {META_PIXEL_ID && (
          <>
            <Script id="meta-pixel-init" strategy="afterInteractive">
              {`
                !function(f,b,e,v,n,t,s)
                {if(f.fbq)return;n=f.fbq=function(){n.callMethod?
                n.callMethod.apply(n,arguments):n.queue.push(arguments)};
                if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
                n.queue=[];t=b.createElement(e);t.async=!0;
                t.src=v;s=b.getElementsByTagName(e)[0];
                s.parentNode.insertBefore(t,s)}(window, document,'script',
                'https://connect.facebook.net/en_US/fbevents.js');
                fbq('init', '${META_PIXEL_ID}');
                fbq('track', 'PageView');
              `}
            </Script>
            <noscript>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                height="1"
                width="1"
                style={{ display: "none" }}
                alt=""
                src={`https://www.facebook.com/tr?id=${META_PIXEL_ID}&ev=PageView&noscript=1`}
              />
            </noscript>
          </>
        )}
      </body>
    </html>
  );
}

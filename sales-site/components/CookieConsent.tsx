"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import Script from "next/script";

// ---------------------------------------------------------------------------
// Bandeau de consentement cookies, requis dès qu'un des deux pixels
// publicitaires (Meta / Google) est activé — voir app/layout.tsx. Les deux
// posent des cookies tiers non strictement nécessaires (fbp/fbc, _ga...),
// contrairement à l'unique cookie de session du pilote LRS.
//
// Comportement :
// - Si ni metaPixelId ni gtagId ne sont configurés, ce composant ne rend
//   rien du tout — pas de cookie tiers en jeu, donc rien à consentir.
// - Sinon, tant que l'utilisateur n'a pas choisi, AUCUN script pixel ne se
//   charge (le consentement doit précéder le dépôt du cookie, pas juste
//   informer après coup) — seul le bandeau s'affiche.
// - "Accepter" : injecte les scripts (via next/script) et mémorise le choix.
// - "Refuser" : n'injecte rien, mémorise le choix pour ne plus redemander.
// - Le choix est stocké en localStorage (par navigateur, jamais transmis
//   au serveur) et relu au chargement suivant.
// ---------------------------------------------------------------------------

const STORAGE_KEY = "lrs_cookie_consent"; // "accepted" | "rejected"

type Consent = "unknown" | "accepted" | "rejected";

const COPY = {
  en: {
    text:
      "We use cookies to measure ad performance (Meta & Google). Accept to help us understand what's working, or decline — the rest of the site works exactly the same either way.",
    details: "What we use",
    detailsBody:
      "Meta Pixel and Google Ads/Analytics, only if you accept. No cookie is set until you choose.",
    accept: "Accept",
    reject: "Decline",
  },
  fr: {
    text:
      "Nous utilisons des cookies pour mesurer la performance de nos publicités (Meta & Google). Acceptez pour nous aider à comprendre ce qui fonctionne, ou refusez — le reste du site fonctionne exactement pareil.",
    details: "Ce qu'on utilise",
    detailsBody:
      "Meta Pixel et Google Ads/Analytics, uniquement si vous acceptez. Aucun cookie n'est déposé tant que vous n'avez pas choisi.",
    accept: "Accepter",
    reject: "Refuser",
  },
};

export default function CookieConsent({
  metaPixelId,
  gtagId,
}: {
  metaPixelId: string;
  gtagId: string;
}) {
  const pathname = usePathname();
  const lang = pathname?.startsWith("/vente/fr") ? "fr" : "en";
  const t = COPY[lang];

  const [consent, setConsent] = useState<Consent>("unknown");
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    let stored: string | null = null;
    try {
      stored = localStorage.getItem(STORAGE_KEY);
    } catch {
      // localStorage indisponible (navigation privée stricte, etc.) —
      // on retombe sur le comportement le plus sûr : redemander à chaque
      // visite plutôt que de planter.
    }
    setConsent(stored === "accepted" || stored === "rejected" ? stored : "unknown");
    setHydrated(true);
  }, []);

  if (!metaPixelId && !gtagId) return null; // rien à consentir
  if (!hydrated) return null; // évite tout flash/mismatch avant lecture du localStorage

  function choose(value: "accepted" | "rejected") {
    try {
      localStorage.setItem(STORAGE_KEY, value);
    } catch {
      // si le stockage échoue, le choix vaut au moins pour cette page —
      // le bandeau reviendra à la prochaine visite, ce n'est pas grave.
    }
    setConsent(value);
  }

  return (
    <>
      {consent === "accepted" && (
        <>
          {gtagId && (
            <>
              <Script
                src={`https://www.googletagmanager.com/gtag/js?id=${gtagId}`}
                strategy="afterInteractive"
              />
              <Script id="gtag-init" strategy="afterInteractive">
                {`
                  window.dataLayer = window.dataLayer || [];
                  function gtag(){dataLayer.push(arguments);}
                  gtag('js', new Date());
                  gtag('config', '${gtagId}');
                `}
              </Script>
            </>
          )}
          {metaPixelId && (
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
                  fbq('init', '${metaPixelId}');
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
                  src={`https://www.facebook.com/tr?id=${metaPixelId}&ev=PageView&noscript=1`}
                />
              </noscript>
            </>
          )}
        </>
      )}

      {consent === "unknown" && (
        <div className="fixed inset-x-0 bottom-0 z-[60] px-4 pb-4 sm:px-6 sm:pb-6">
          <div className="mx-auto flex max-w-2xl flex-col gap-3 rounded-2xl border border-black/10 bg-white/95 p-5 shadow-[0_8px_32px_rgba(0,0,0,0.12)] backdrop-blur sm:flex-row sm:items-center sm:gap-5">
            <div className="flex-1 text-sm leading-relaxed text-[#1d1d1f]">
              <p>{t.text}</p>
              <details className="mt-1.5">
                <summary className="cursor-pointer text-xs font-semibold text-[#007aff]">
                  {t.details}
                </summary>
                <p className="mt-1 text-xs leading-relaxed text-[#86868b]">
                  {t.detailsBody}
                </p>
              </details>
            </div>
            <div className="flex shrink-0 gap-2">
              <button
                onClick={() => choose("rejected")}
                className="rounded-full border border-black/15 bg-white px-5 py-2.5 text-sm font-semibold text-[#1d1d1f] transition hover:bg-black/5"
              >
                {t.reject}
              </button>
              <button
                onClick={() => choose("accepted")}
                className="rounded-full bg-[#007aff] px-5 py-2.5 text-sm font-semibold text-white shadow-[0_4px_14px_rgba(0,122,255,0.35)] transition hover:bg-[#0066d6]"
              >
                {t.accept}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

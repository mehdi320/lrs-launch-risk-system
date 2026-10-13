import { NextRequest, NextResponse } from "next/server";

// ---------------------------------------------------------------------------
// CSP en mode Report-Only — étape 1 du plan (Report-Only -> ajustement ->
// bloquant -> test d'achat, voir scratchpad session 2026-10-12). Observe les
// violations sans jamais bloquer une ressource, pour valider la politique en
// conditions réelles avant de passer en mode bloquant.
//
// NE PAS passer en `Content-Security-Policy` (bloquant) sans un test
// d'achat réel bout en bout d'abord — le bouton Stripe (buy-button.js, puis
// l'iframe/les appels réseau qu'il déclenche) n'a jamais été vérifié sous
// cette politique.
//
// Nonce par requête : propagé via le header `x-nonce` (lu dans
// app/layout.tsx avec `headers()` et passé aux <Script> que nous
// contrôlons) et injecté automatiquement par Next.js dans ses propres
// scripts internes dès qu'il détecte ce nonce dans l'en-tête CSP sortant —
// mécanisme documenté par Next.js pour le App Router.
export function middleware(request: NextRequest) {
  const nonce = Buffer.from(crypto.randomUUID()).toString("base64");

  const cspHeader = `
    default-src 'self';
    script-src 'self' 'nonce-${nonce}' https://www.googletagmanager.com https://connect.facebook.net https://js.stripe.com;
    style-src 'self' 'unsafe-inline';
    img-src 'self' data: https://www.facebook.com;
    font-src 'self';
    connect-src 'self' https://www.google-analytics.com https://www.googletagmanager.com https://api.stripe.com https://m.stripe.com;
    frame-src https://js.stripe.com https://hooks.stripe.com https://checkout.stripe.com;
    object-src 'none';
    base-uri 'self';
    form-action 'self';
    frame-ancestors 'none';
  `;
  // upgrade-insecure-requests est omise ici : Chrome l'ignore et log un
  // avertissement en mode Report-Only ("ignored when delivered in a
  // report-only policy"), testé directement. À ajouter à la ligne
  // ci-dessus seulement au passage en mode bloquant.
  const contentSecurityPolicyHeaderValue = cspHeader
    .replace(/\s{2,}/g, " ")
    .trim();

  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-nonce", nonce);
  requestHeaders.set(
    "Content-Security-Policy-Report-Only",
    contentSecurityPolicyHeaderValue
  );

  const response = NextResponse.next({
    request: { headers: requestHeaders },
  });
  response.headers.set(
    "Content-Security-Policy-Report-Only",
    contentSecurityPolicyHeaderValue
  );

  return response;
}

export const config = {
  matcher: [
    // Toutes les routes sauf les assets statiques internes de Next.
    "/((?!_next/static|_next/image|favicon.ico).*)",
  ],
};

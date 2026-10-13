// Chargé uniquement après acceptation du bandeau cookies (voir
// components/CookieConsent.tsx) et uniquement si NEXT_PUBLIC_GTAG_ID est
// renseigné (voir app/layout.tsx). Externalisé plutôt qu'inline pour
// permettre une CSP script-src 'self' + domaines tiers explicites, sans
// 'unsafe-inline' — même logique que pilot_server.py et
// creative_studio/serving/app.py pour leurs propres pages.
(function () {
  var gtagId = document.currentScript.getAttribute("data-gtag-id");
  if (!gtagId) return;
  window.dataLayer = window.dataLayer || [];
  function gtag() {
    window.dataLayer.push(arguments);
  }
  gtag("js", new Date());
  gtag("config", gtagId);
  window.gtag = gtag;
})();

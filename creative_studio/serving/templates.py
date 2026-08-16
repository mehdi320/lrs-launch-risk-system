"""Rendu HTML minimal d'une variante (advertorial / page de vente).

Volontairement simple (pas de moteur de template externe) : le contenu
vient du CopyBlock structuré généré par Claude, échappé par précaution
avant injection dans le HTML. Médias (FunnelStepMedia) et éléments de
conversion (FunnelStepElement) sont optionnels — une variante hors Funnel
Builder n'en a jamais, une étape de funnel qui en a les reçoit ici et à
l'export PDF (core/pdf_export.py) via le même contenu textuel
(core.funnel_elements.render_element_text) ; seule cette page ajoute un
décompte JS live pour les éléments datés, le PDF restant statique par
nature.
"""

from __future__ import annotations

from html import escape
from typing import Iterable

from creative_studio.core.funnel_elements import countdown_target_iso, render_element_text
from creative_studio.core.variants import (
    FunnelStepElement,
    FunnelStepMedia,
    MediaPlacement,
    MediaSourceType,
    MediaType,
    Product,
    Variant,
)

_PAGE_TEMPLATE = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{headline}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          max-width: 680px; margin: 0 auto; padding: 32px 20px 96px; line-height: 1.55;
          color: #1a1a2e; background: #fff; }}
  h1 {{ font-size: 1.9rem; margin-bottom: 0.4em; }}
  .hook {{ font-size: 1.1rem; color: #444; margin-bottom: 1.6em; }}
  .section {{ margin-bottom: 1.2em; white-space: pre-wrap; }}
  .price {{ font-weight: 700; }}
  .cta {{ display: block; text-align: center; background: #6366f1; color: #fff;
          font-weight: 700; font-size: 1.1rem; padding: 16px 24px; border-radius: 10px;
          text-decoration: none; margin-top: 2em; }}
  .cta:hover {{ background: #4f46e5; }}
  .funnel-media {{ max-width: 100%; border-radius: 10px; margin: 1.2em 0; display: block; }}
  .funnel-element {{ background: #f3f4f6; border-radius: 8px; padding: 10px 14px;
                      margin: 0.8em 0; font-weight: 600; color: #1a1a2e; }}
</style>
</head>
<body>
  {hero_media}
  <h1>{headline}</h1>
  <p class="hook">{hook}</p>
  {demo_media}
  {sections}
  {proof_media}
  {elements}
  <p class="price">{price} {currency}</p>
  <a class="cta" href="{cta_url}">{cta}</a>
  {countdown_script}
</body>
</html>
"""

# Un seul script partagé par page, injecté seulement si au moins un élément
# daté (timer/réduction limitée) est présent — anime le <span> statique de
# _elements_html sans dupliquer le texte de secours (render_element_text
# reste affiché tel quel si JS est désactivé).
_COUNTDOWN_SCRIPT = """<script>
(function () {
  function fmt(diffMs) {
    if (diffMs <= 0) return "Expiré";
    var s = Math.floor(diffMs / 1000);
    var d = Math.floor(s / 86400); s -= d * 86400;
    var h = Math.floor(s / 3600); s -= h * 3600;
    var m = Math.floor(s / 60); s -= m * 60;
    return d + "j " + h + "h " + m + "m " + s + "s";
  }
  document.querySelectorAll('[data-countdown-target]').forEach(function (el) {
    var target = new Date(el.dataset.countdownTarget).getTime();
    var span = el.querySelector('.lrs-countdown-static');
    if (!span || isNaN(target)) return;
    var idx = span.textContent.lastIndexOf(":");
    var prefix = idx >= 0 ? span.textContent.slice(0, idx) : span.textContent;
    function tick() {
      span.textContent = prefix + ": " + fmt(target - Date.now());
    }
    tick();
    setInterval(tick, 1000);
  });
})();
</script>"""


def _media_src(media: FunnelStepMedia) -> str:
    if media.source_type == MediaSourceType.UPLOAD:
        return f"/media/{media.location}"
    return media.location


def _media_html(media_items: Iterable[FunnelStepMedia]) -> str:
    parts = []
    for m in media_items:
        src = escape(_media_src(m), quote=True)
        if m.media_type == MediaType.VIDEO:
            parts.append(f'<video class="funnel-media" src="{src}" controls></video>')
        else:
            parts.append(f'<img class="funnel-media" src="{src}" alt="">')
    return "\n".join(parts)


def _elements_html(elements: Iterable[FunnelStepElement]) -> tuple[str, str]:
    """Retourne (html des éléments, script JS ou chaîne vide). Le texte
    statique de render_element_text() fait toujours foi comme contenu
    initial/fallback ; le script anime en plus les éléments datés en
    remplaçant leur <span> une fois chargé côté visiteur."""
    parts = []
    has_countdown = False
    for el in elements:
        if not el.enabled:
            continue
        text = render_element_text(el.element_type, el.config)
        if not text:
            continue
        target = countdown_target_iso(el.element_type, el.config)
        if target:
            has_countdown = True
            parts.append(
                f'<p class="funnel-element" data-countdown-target="{escape(target, quote=True)}">'
                f'<span class="lrs-countdown-static">{escape(text)}</span></p>'
            )
        else:
            parts.append(f'<p class="funnel-element">{escape(text)}</p>')
    return "\n".join(parts), (_COUNTDOWN_SCRIPT if has_countdown else "")


def render_variant_page(
    variant: Variant,
    product: Product,
    cta_url: str,
    media: list[FunnelStepMedia] | None = None,
    elements: list[FunnelStepElement] | None = None,
) -> str:
    media = media or []
    elements = elements or []

    sections_html = "\n".join(
        f'  <p class="section">{escape(section)}</p>' for section in variant.copy.body_sections
    )
    elements_html, script_html = _elements_html(elements)

    return _PAGE_TEMPLATE.format(
        headline=escape(variant.copy.headline),
        hero_media=_media_html(m for m in media if m.placement == MediaPlacement.HERO),
        hook=escape(variant.copy.hook),
        demo_media=_media_html(m for m in media if m.placement == MediaPlacement.DEMO),
        sections=sections_html,
        proof_media=_media_html(m for m in media if m.placement == MediaPlacement.PROOF),
        elements=elements_html,
        price=f"{product.price_cents / 100:.2f}",
        currency=escape(product.currency),
        cta_url=escape(cta_url, quote=True),
        cta=escape(variant.copy.cta),
        countdown_script=script_html,
    )

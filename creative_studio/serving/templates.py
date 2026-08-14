"""Rendu HTML minimal d'une variante (advertorial / page de vente).

Volontairement simple (pas de moteur de template externe) : le contenu
vient du CopyBlock structuré généré par Claude, échappé par précaution
avant injection dans le HTML.
"""

from __future__ import annotations

from html import escape

from creative_studio.core.variants import Product, Variant

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
</style>
</head>
<body>
  <h1>{headline}</h1>
  <p class="hook">{hook}</p>
  {sections}
  <p class="price">{price} {currency}</p>
  <a class="cta" href="{cta_url}">{cta}</a>
</body>
</html>
"""


def render_variant_page(variant: Variant, product: Product, cta_url: str) -> str:
    sections_html = "\n".join(
        f'  <p class="section">{escape(section)}</p>' for section in variant.copy.body_sections
    )
    return _PAGE_TEMPLATE.format(
        headline=escape(variant.copy.headline),
        hook=escape(variant.copy.hook),
        sections=sections_html,
        price=f"{product.price_cents / 100:.2f}",
        currency=escape(product.currency),
        cta_url=escape(cta_url, quote=True),
        cta=escape(variant.copy.cta),
    )

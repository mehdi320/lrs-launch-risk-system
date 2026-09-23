"""Rendu HTML minimal d'une variante (advertorial / page de vente).

Volontairement simple (pas de moteur de template externe) : le contenu
vient du CopyBlock structuré généré par Claude, échappé par précaution
avant injection dans le HTML. Médias (FunnelStepMedia), éléments de
conversion (FunnelStepElement), formulaire multi-étapes (FunnelStepForm) et
popup exit-intent (FunnelStepPopup) sont tous optionnels — une variante hors
Funnel Builder n'en a jamais ; le PDF (core/pdf_export.py) reste, lui,
statique par nature (pas de formulaire ni de popup dans un PDF).
"""

from __future__ import annotations

from html import escape
from typing import Iterable

from creative_studio.core.funnel_elements import countdown_target_iso, render_element_text
from creative_studio.core.variants import (
    FunnelStepElement,
    FunnelStepForm,
    FunnelStepMedia,
    FunnelStepPopup,
    MediaPlacement,
    MediaSourceType,
    MediaType,
    PopupMode,
    Product,
    Variant,
)

_PAGE_TEMPLATE = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{headline}</title>
<link rel="stylesheet" href="/static/css/funnel-page.css">
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
  {cta_block}
  {popup}
  {scripts}
</body>
</html>
"""

# Un seul script par mécanisme, injecté seulement si le composant
# correspondant est présent sur la page — le texte statique
# (render_element_text pour les éléments, le CopyBlock pour le popup) fait
# toujours foi comme contenu de secours si JS est désactivé.
#
# Fichiers externes (static/js/) plutôt qu'inline : permet une CSP
# script-src 'self' stricte côté serving/app.py, sans 'unsafe-inline' ni
# hash à régénérer à chaque édition de ces scripts.
_COUNTDOWN_SCRIPT = '<script src="/static/js/countdown.js"></script>'
_FORM_SCRIPT = '<script src="/static/js/form-nav.js"></script>'
_EXIT_INTENT_SCRIPT = '<script src="/static/js/exit-intent.js"></script>'


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


def _elements_html(elements: Iterable[FunnelStepElement]) -> tuple[str, bool]:
    """Retourne (html des éléments, présence d'au moins un élément daté) —
    le script correspondant est ajouté par l'appelant si besoin."""
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
    return "\n".join(parts), has_countdown


def _form_html(form: FunnelStepForm | None, cta_label: str, submit_url: str) -> str:
    """Formulaire découpé en plusieurs écrans successifs — un seul écran
    visible à la fois (le JS de _FORM_SCRIPT révèle le suivant), le dernier
    portant le vrai bouton de soumission avec le texte de CTA de la page."""
    if form is None or not form.enabled or not form.screens:
        return ""
    screens_html = []
    total = len(form.screens)
    for i, screen in enumerate(form.screens):
        fields_html = "".join(
            f'<label class="lrs-form-label">{escape(f.label)}'
            f'<input class="lrs-form-input" type="{escape(f.field_type.value, quote=True)}" '
            f'name="{escape(f.name, quote=True)}"{" required" if f.required else ""}></label>'
            for f in screen
        )
        is_last = i == total - 1
        action_html = (
            f'<button type="submit" class="cta">{escape(cta_label)}</button>'
            if is_last else
            '<button type="button" class="lrs-form-next" data-lrs-action="form-next">Suivant</button>'
        )
        hidden_attr = "" if i == 0 else " hidden"
        screens_html.append(f'<div class="lrs-form-screen"{hidden_attr}>{fields_html}{action_html}</div>')
    return (
        f'<form class="lrs-form" method="post" action="{escape(submit_url, quote=True)}">'
        '<input type="hidden" name="__lrs_source" value="page">'
        + "".join(screens_html) + "</form>"
    )


def _popup_html(popup: FunnelStepPopup | None, cta_url: str, submit_url: str) -> str:
    if popup is None or not popup.enabled:
        return ""
    body_html = "".join(f"<p>{escape(s)}</p>" for s in popup.copy.body_sections)
    if popup.mode == PopupMode.EMAIL_CAPTURE:
        action_html = (
            f'<form method="post" action="{escape(submit_url, quote=True)}" class="lrs-form">'
            '<input type="hidden" name="__lrs_source" value="exit_popup">'
            '<input class="lrs-form-input" type="email" name="email" placeholder="Votre email" required>'
            f'<button type="submit" class="cta">{escape(popup.copy.cta)}</button>'
            "</form>"
        )
    else:
        action_html = f'<a class="cta" href="{escape(cta_url, quote=True)}">{escape(popup.copy.cta)}</a>'
    return (
        '<div id="lrs-exit-popup" class="lrs-popup-overlay" hidden>'
        '<div class="lrs-popup-card">'
        '<button type="button" class="lrs-popup-close" '
        'data-lrs-action="close-popup">×</button>'
        f"<h2>{escape(popup.copy.headline)}</h2>"
        f"<p>{escape(popup.copy.hook)}</p>"
        f"{body_html}{action_html}"
        "</div></div>"
    )


def render_variant_page(
    variant: Variant,
    product: Product,
    cta_url: str,
    media: list[FunnelStepMedia] | None = None,
    elements: list[FunnelStepElement] | None = None,
    form: FunnelStepForm | None = None,
    popup: FunnelStepPopup | None = None,
    submit_url: str | None = None,
) -> str:
    """`submit_url` est requis si `form` et/ou `popup` (mode email_capture)
    sont fournis — cible du POST de soumission (voir serving/app.py). Quand
    un formulaire actif est attaché, il remplace le lien CTA classique (son
    dernier écran porte déjà le bouton de soumission avec le même texte)."""
    media = media or []
    elements = elements or []

    sections_html = "\n".join(
        f'  <p class="section">{escape(section)}</p>' for section in variant.copy.body_sections
    )
    elements_html, has_countdown = _elements_html(elements)
    form_html = _form_html(form, variant.copy.cta, submit_url or "") if submit_url else ""
    popup_html = _popup_html(popup, cta_url, submit_url or "")

    cta_block = form_html or f'<a class="cta" href="{escape(cta_url, quote=True)}">{escape(variant.copy.cta)}</a>'

    scripts = []
    if has_countdown:
        scripts.append(_COUNTDOWN_SCRIPT)
    if form_html:
        scripts.append(_FORM_SCRIPT)
    if popup_html:
        scripts.append(_EXIT_INTENT_SCRIPT)

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
        cta_block=cta_block,
        popup=popup_html,
        scripts="\n".join(scripts),
    )

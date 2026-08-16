"""Export PDF du copy gagnant (variante seule ou funnel complet).

Contenu uniquement — pas de métadonnées de test, pas de branding LRS : le
texte généré doit être copiable tel quel dans Meta Ads Manager, Shopify, ou
n'importe quel éditeur. Généré à la volée en mémoire (io.BytesIO), jamais
écrit sur disque — reportlab est déjà une dépendance du dépôt (voir
lrs_pdf_report.py à la racine).

Médias (FunnelStepMedia) et éléments de conversion (FunnelStepElement) sont
optionnels : un PDF de variante seule (hors Funnel Builder) n'en a jamais,
un PDF de funnel les inclut quand ils sont attachés à l'étape correspondante.
Le PDF est forcément statique — une vidéo attachée est listée en lien
copiable, pas jouée ; un timer/une réduction datée est affiché en texte figé
(render_element_text), sans le décompte JS live de la page servie.
"""

from __future__ import annotations

import io
import re
from datetime import datetime, timezone
from xml.sax.saxutils import escape as _xml_escape

import requests
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image as ReportlabImage
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

from creative_studio.core.copy_generation import KIND_LABELS
from creative_studio.core.funnel_elements import render_element_text
from creative_studio.core.variants import (
    Funnel,
    FunnelStepElement,
    FunnelStepMedia,
    MediaSourceType,
    MediaType,
    Product,
    Variant,
)
from creative_studio.storage.media import media_path

__all__ = [
    "build_funnel_pdf_filename",
    "build_pdf_filename",
    "generate_funnel_pdf",
    "generate_variant_pdf",
]

_MAX_IMAGE_WIDTH_CM = 15
_MAX_IMAGE_HEIGHT_CM = 10


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.strip().lower()).strip("_")
    return slug or "produit"


def _escape(text: str) -> str:
    """Échappe le texte pour le mini-markup XML de reportlab (Paragraph
    interprète &, < et > comme des balises) et convertit les retours à la
    ligne en <br/> — le copy vient de Claude, pas d'un template contrôlé."""
    return _xml_escape(text).replace("\n", "<br/>")


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "step_title": ParagraphStyle(
            "StepTitle", parent=base["Heading2"], fontSize=12, leading=15,
            spaceBefore=4, spaceAfter=10, textColor=colors.HexColor("#555555"),
        ),
        "headline": ParagraphStyle(
            "Headline", parent=base["Title"], fontSize=18, leading=22,
            spaceAfter=12, alignment=0,
        ),
        "hook": ParagraphStyle(
            "Hook", parent=base["BodyText"], fontSize=12, leading=16,
            spaceAfter=14, fontName="Helvetica-Oblique",
        ),
        "body": ParagraphStyle(
            "Body", parent=base["BodyText"], fontSize=11, leading=16, spaceAfter=10,
        ),
        "media_note": ParagraphStyle(
            "MediaNote", parent=base["BodyText"], fontSize=9, leading=13,
            spaceAfter=8, textColor=colors.HexColor("#888888"), fontName="Helvetica-Oblique",
        ),
        "element": ParagraphStyle(
            "Element", parent=base["BodyText"], fontSize=11, leading=15,
            spaceBefore=4, spaceAfter=8, fontName="Helvetica-Bold",
            textColor=colors.HexColor("#1a1a2e"), backColor=colors.HexColor("#f3f4f6"),
            borderPadding=6,
        ),
        "cta": ParagraphStyle(
            "CTA", parent=base["BodyText"], fontSize=13, leading=17,
            spaceBefore=10, fontName="Helvetica-Bold",
        ),
    }


def _image_bytes(media: FunnelStepMedia) -> bytes | None:
    """Récupère les bytes d'une image (upload local ou téléchargement URL) —
    None si indisponible plutôt que de faire échouer tout le PDF pour un
    média cassé (lien mort, fichier supprimé sur disque)."""
    try:
        if media.source_type == MediaSourceType.UPLOAD:
            with open(media_path(media.location), "rb") as f:
                return f.read()
        response = requests.get(media.location, timeout=15)
        response.raise_for_status()
        return response.content
    except Exception:
        return None


def _media_flowables(media_items: list[FunnelStepMedia], styles: dict[str, ParagraphStyle]) -> list:
    flowables = []
    for m in media_items:
        if m.media_type == MediaType.VIDEO:
            flowables.append(Paragraph(_escape(f"🎥 Vidéo : {m.location}"), styles["media_note"]))
            continue
        data = _image_bytes(m)
        if data is None:
            flowables.append(Paragraph(_escape("[image indisponible]"), styles["media_note"]))
            continue
        try:
            width_px, height_px = PILImage.open(io.BytesIO(data)).size
            max_w, max_h = _MAX_IMAGE_WIDTH_CM * cm, _MAX_IMAGE_HEIGHT_CM * cm
            scale = min(max_w / width_px, max_h / height_px, 1.0)
            flowables.append(ReportlabImage(io.BytesIO(data), width=width_px * scale, height=height_px * scale))
            flowables.append(Spacer(1, 8))
        except Exception:
            flowables.append(Paragraph(_escape("[image indisponible]"), styles["media_note"]))
    return flowables


def _variant_flowables(
    variant: Variant,
    styles: dict[str, ParagraphStyle],
    media: list[FunnelStepMedia] | None = None,
    elements: list[FunnelStepElement] | None = None,
) -> list:
    media = media or []
    elements = elements or []
    hero = [m for m in media if m.placement.value == "hero"]
    demo = [m for m in media if m.placement.value == "demo"]
    proof = [m for m in media if m.placement.value == "proof"]

    flowables = []
    flowables.extend(_media_flowables(hero, styles))
    flowables.append(Paragraph(_escape(variant.copy.headline), styles["headline"]))
    flowables.append(Paragraph(_escape(variant.copy.hook), styles["hook"]))
    flowables.extend(_media_flowables(demo, styles))
    for section in variant.copy.body_sections:
        flowables.append(Paragraph(_escape(section), styles["body"]))
    flowables.extend(_media_flowables(proof, styles))
    for element in elements:
        if not element.enabled:
            continue
        text = render_element_text(element.element_type, element.config)
        if text:
            flowables.append(Paragraph(_escape(text), styles["element"]))
    flowables.append(Spacer(1, 8))
    flowables.append(Paragraph(_escape(variant.copy.cta), styles["cta"]))
    return flowables


def build_pdf_filename(product: Product) -> str:
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"{_slugify(product.name)}_variante_gagnante_{date_str}.pdf"


def generate_variant_pdf(
    product: Product,
    variant: Variant,
    media: list[FunnelStepMedia] | None = None,
    elements: list[FunnelStepElement] | None = None,
) -> bytes:
    """PDF prêt à copier-coller pour une seule variante gagnante : le copy
    final (headline, hook, corps, CTA), plus médias/éléments de conversion
    optionnels si cette variante est une étape de funnel qui en a."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2.5 * cm, rightMargin=2.5 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
    )
    doc.build(_variant_flowables(variant, _styles(), media, elements))
    return buf.getvalue()


def build_funnel_pdf_filename(product: Product, funnel: Funnel) -> str:
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"{_slugify(product.name)}_funnel_{funnel.objective.value}_{date_str}.pdf"


def generate_funnel_pdf(
    product: Product,
    funnel: Funnel,
    variants_in_order: list[Variant],
    media_by_variant_id: dict[str, list[FunnelStepMedia]] | None = None,
    elements_by_variant_id: dict[str, list[FunnelStepElement]] | None = None,
) -> bytes:
    """PDF unique regroupant toutes les étapes du funnel, clairement séparées
    (saut de page entre chaque étape) et copiables une par une, avec les
    médias et éléments de conversion attachés à chaque étape."""
    media_by_variant_id = media_by_variant_id or {}
    elements_by_variant_id = elements_by_variant_id or {}
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2.5 * cm, rightMargin=2.5 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
    )
    styles = _styles()
    story = []
    total = len(variants_in_order)
    for i, variant in enumerate(variants_in_order, start=1):
        kind_label = KIND_LABELS.get(variant.kind, variant.kind.value)
        story.append(Paragraph(_escape(f"Étape {i}/{total} — {kind_label}"), styles["step_title"]))
        story.extend(
            _variant_flowables(
                variant, styles,
                media_by_variant_id.get(variant.id), elements_by_variant_id.get(variant.id),
            )
        )
        if i < total:
            story.append(PageBreak())
    doc.build(story)
    return buf.getvalue()

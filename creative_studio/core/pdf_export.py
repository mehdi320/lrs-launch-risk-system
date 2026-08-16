"""Export PDF du copy gagnant (variante seule ou funnel complet).

Contenu uniquement — pas de métadonnées de test, pas de branding LRS : le
texte généré doit être copiable tel quel dans Meta Ads Manager, Shopify, ou
n'importe quel éditeur. Généré à la volée en mémoire (io.BytesIO), jamais
écrit sur disque — reportlab est déjà une dépendance du dépôt (voir
lrs_pdf_report.py à la racine).
"""

from __future__ import annotations

import io
import re
from datetime import datetime, timezone
from xml.sax.saxutils import escape as _xml_escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

from creative_studio.core.copy_generation import KIND_LABELS
from creative_studio.core.variants import Funnel, Product, Variant

__all__ = [
    "build_funnel_pdf_filename",
    "build_pdf_filename",
    "generate_funnel_pdf",
    "generate_variant_pdf",
]


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
        "cta": ParagraphStyle(
            "CTA", parent=base["BodyText"], fontSize=13, leading=17,
            spaceBefore=10, fontName="Helvetica-Bold",
        ),
    }


def _variant_flowables(variant: Variant, styles: dict[str, ParagraphStyle]) -> list:
    flowables = [
        Paragraph(_escape(variant.copy.headline), styles["headline"]),
        Paragraph(_escape(variant.copy.hook), styles["hook"]),
    ]
    for section in variant.copy.body_sections:
        flowables.append(Paragraph(_escape(section), styles["body"]))
    flowables.append(Spacer(1, 8))
    flowables.append(Paragraph(_escape(variant.copy.cta), styles["cta"]))
    return flowables


def build_pdf_filename(product: Product) -> str:
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"{_slugify(product.name)}_variante_gagnante_{date_str}.pdf"


def generate_variant_pdf(product: Product, variant: Variant) -> bytes:
    """PDF prêt à copier-coller pour une seule variante gagnante : juste le
    copy final (headline, hook, corps, CTA), sans aucune métadonnée de test."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2.5 * cm, rightMargin=2.5 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
    )
    doc.build(_variant_flowables(variant, _styles()))
    return buf.getvalue()


def build_funnel_pdf_filename(product: Product, funnel: Funnel) -> str:
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"{_slugify(product.name)}_funnel_{funnel.objective.value}_{date_str}.pdf"


def generate_funnel_pdf(product: Product, funnel: Funnel, variants_in_order: list[Variant]) -> bytes:
    """PDF unique regroupant toutes les étapes du funnel, clairement séparées
    (saut de page entre chaque étape) et copiables une par une."""
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
        story.extend(_variant_flowables(variant, styles))
        if i < total:
            story.append(PageBreak())
    doc.build(story)
    return buf.getvalue()

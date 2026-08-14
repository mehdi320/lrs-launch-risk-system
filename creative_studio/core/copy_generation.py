"""Génération de copy (advertorials / pages de vente) via l'API Claude.

Utilise des sorties structurées (output_config.format) pour récupérer
directement un CopyBlock exploitable, sans parsing regex fragile. Le
contenu des frameworks de copywriting (methodology_copywriting.txt) est
mis en cache côté prompt (cache_control) car il est identique d'un
appel à l'autre.
"""

from __future__ import annotations

import json
import os

from creative_studio.core.llm_client import GenerationRefused, build_client, get_anthropic_api_key
from creative_studio.core.variants import CopyBlock, Framework, Product, Variant, VariantKind

_METHODOLOGY_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "methodology_copywriting.txt"
)

DEFAULT_MODEL = "claude-opus-5"

__all__ = [
    "DEFAULT_MODEL",
    "GenerationRefused",
    "generate_variant",
    "generate_variants",
    "get_anthropic_api_key",
]

_COPY_SCHEMA = {
    "type": "object",
    "properties": {
        "headline": {
            "type": "string",
            "description": "Titre principal, accrocheur, aligné avec le framework demandé",
        },
        "hook": {
            "type": "string",
            "description": "Première phrase / accroche qui capte l'attention (étape Attention/Problem du framework)",
        },
        "body_sections": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Sections de corps de texte, dans l'ordre de lecture, développant le framework demandé",
        },
        "cta": {"type": "string", "description": "Appel à l'action final, une seule action"},
    },
    "required": ["headline", "hook", "body_sections", "cta"],
    "additionalProperties": False,
}


def _load_methodology() -> str:
    if os.path.exists(_METHODOLOGY_PATH):
        with open(_METHODOLOGY_PATH, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def _system_prompt() -> list[dict]:
    methodology = _load_methodology()
    return [
        {
            "type": "text",
            "text": (
                "Tu es un copywriter direct-response expert en produits digitaux. "
                "Tu génères des advertorials et pages de vente en t'appuyant strictement "
                "sur les frameworks de copywriting fournis ci-dessous. "
                "Réponds uniquement avec le contenu demandé, sans commentaire méta.\n\n"
                + methodology
            ),
            "cache_control": {"type": "ephemeral"},
        }
    ]


def generate_variant(
    product: Product,
    kind: VariantKind,
    framework: Framework,
    model: str = DEFAULT_MODEL,
) -> Variant:
    """Génère une variante (copy structuré) pour un produit et un framework donnés."""
    client = build_client()

    kind_label = "advertorial" if kind == VariantKind.ADVERTORIAL else "page de vente"
    user_prompt = (
        f"Génère un {kind_label} en utilisant le framework {framework.value}.\n\n"
        f"Produit : {product.name}\n"
        f"Description : {product.description}\n"
        f"Prix : {product.price_cents / 100:.2f} {product.currency}\n"
        f"Cible / audience : {product.audience}\n"
    )

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=_system_prompt(),
        thinking={"type": "adaptive"},
        output_config={
            "effort": "high",
            "format": {"type": "json_schema", "schema": _COPY_SCHEMA},
        },
        messages=[{"role": "user", "content": user_prompt}],
    )

    if response.stop_reason == "refusal":
        category = getattr(response.stop_details, "category", None) if response.stop_details else None
        raise GenerationRefused(f"Génération refusée par Claude (catégorie: {category})")

    text_block = next(b for b in response.content if b.type == "text")
    data = json.loads(text_block.text)
    copy = CopyBlock(**data)

    return Variant(product_id=product.id, kind=kind, framework=framework, copy=copy)


def generate_variants(
    product: Product,
    kind: VariantKind,
    frameworks: list[Framework] | None = None,
    model: str = DEFAULT_MODEL,
) -> list[Variant]:
    """Génère une variante par framework (3 par défaut : AIDA, PAS, Hormozi)."""
    frameworks = frameworks or [Framework.AIDA, Framework.PAS, Framework.HORMOZI]
    return [generate_variant(product, kind, fw, model=model) for fw in frameworks]

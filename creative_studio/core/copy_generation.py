"""Génération de copy (advertorials / pages de vente) via l'API Claude.

Deux modes d'entrée, un seul cœur de génération commun :
- "from scratch" (generate_variant / generate_variants) : input minimal
  (produit, description, prix, audience), aucune référence requise.
- "optimize existing" (generate_variant_from_reference /
  generate_variants_from_reference) : ancré sur l'analyse d'un advertorial
  ou d'une page de vente déjà existante (core.reference_extraction), ne
  fait varier qu'UN seul paramètre à la fois (hook, preuve sociale,
  urgence ou CTA) plutôt que de tout réécrire.

Les deux modes partagent le même schéma de sortie structurée (_COPY_SCHEMA),
le même system prompt (méthodologie de copywriting mise en cache) et le
même appel Claude (_call_claude_for_copy) — seule la construction du prompt
utilisateur change selon le mode. Ils produisent le même objet Variant, donc
aucune duplication de logique de diffusion ou de moteur statistique n'est
nécessaire côté serving/stats : les deux modes alimentent le même pipeline
de test A/B.
"""

from __future__ import annotations

import os

from creative_studio.core.llm_client import (
    DEFAULT_MODEL,
    GenerationRefused,
    build_client,
    get_anthropic_api_key,
    parse_structured_json_response,
)
from creative_studio.core.reference_extraction import VARY_DIMENSION_LABELS, ExistingCopyAnalysis
from creative_studio.core.variants import (
    CopyBlock,
    Framework,
    GenerationMode,
    Product,
    Variant,
    VariantKind,
    VaryDimension,
)

_METHODOLOGY_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "methodology_copywriting.txt"
)

__all__ = [
    "DEFAULT_MODEL",
    "GenerationRefused",
    "generate_variant",
    "generate_variants",
    "generate_variant_from_reference",
    "generate_variants_from_reference",
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


def _call_claude_for_copy(user_prompt: str, model: str) -> CopyBlock:
    """Appel Claude partagé par les deux modes — sortie structurée en CopyBlock.

    C'est la seule fonction qui parle réellement à l'API ; generate_variant
    et generate_variant_from_reference ne diffèrent que par le prompt
    utilisateur qu'elles construisent avant d'appeler cette fonction.
    """
    client = build_client()
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
    data = parse_structured_json_response(response)
    return CopyBlock(**data)


def generate_variant(
    product: Product,
    kind: VariantKind,
    framework: Framework,
    model: str = DEFAULT_MODEL,
) -> Variant:
    """Mode "Créer depuis zéro" : génère une variante à partir du seul input
    produit (nom, description, prix, audience) — aucun advertorial ou
    funnel existant requis.
    """
    kind_label = "advertorial" if kind == VariantKind.ADVERTORIAL else "page de vente"
    user_prompt = (
        f"Génère un {kind_label} en utilisant le framework {framework.value}.\n\n"
        f"Produit : {product.name}\n"
        f"Description : {product.description}\n"
        f"Prix : {product.price_cents / 100:.2f} {product.currency}\n"
        f"Cible / audience : {product.audience}\n"
    )

    copy = _call_claude_for_copy(user_prompt, model)

    return Variant(
        product_id=product.id, kind=kind, framework=framework, copy=copy,
        source_mode=GenerationMode.FROM_SCRATCH,
    )


def generate_variants(
    product: Product,
    kind: VariantKind,
    frameworks: list[Framework] | None = None,
    model: str = DEFAULT_MODEL,
) -> list[Variant]:
    """Mode "Créer depuis zéro" : une variante par framework (3 par défaut :
    AIDA, PAS, Hormozi)."""
    frameworks = frameworks or [Framework.AIDA, Framework.PAS, Framework.HORMOZI]
    return [generate_variant(product, kind, fw, model=model) for fw in frameworks]


def generate_variant_from_reference(
    product: Product,
    kind: VariantKind,
    reference: ExistingCopyAnalysis,
    vary_dimension: VaryDimension,
    model: str = DEFAULT_MODEL,
) -> Variant:
    """Mode "Optimiser un existant" : génère une variante qui préserve
    l'angle, l'offre et la structure d'un advertorial/page de vente déjà
    analysé (core.reference_extraction.analyze_existing_copy), en ne
    faisant varier qu'UNE seule dimension à la fois — pas une réécriture
    totale à chaque variante, pour pouvoir isoler ce qui améliore
    réellement la conversion.
    """
    kind_label = "advertorial" if kind == VariantKind.ADVERTORIAL else "page de vente"
    dimension_label = VARY_DIMENSION_LABELS[vary_dimension.value]
    hybrid_note = f" (hybride : {reference.hybrid_notes})" if reference.is_hybrid else ""

    user_prompt = (
        f"Voici l'analyse d'un {kind_label} existant qui fonctionne déjà "
        f"(framework détecté : {reference.detected_framework.value}{hybrid_note}).\n\n"
        f"Angle d'origine : {reference.angle}\n"
        f"Hook d'origine : {reference.hook}\n"
        f"Structure du corps d'origine : {reference.body_summary}\n"
        f"Preuve sociale d'origine : {reference.social_proof_notes}\n"
        f"Urgence d'origine : {reference.urgency_notes}\n"
        f"CTA d'origine : {reference.cta}\n\n"
        f"Produit : {product.name}\n"
        f"Description : {product.description}\n"
        f"Prix : {product.price_cents / 100:.2f} {product.currency}\n"
        f"Cible / audience : {product.audience}\n\n"
        f"CONSIGNE STRICTE : génère une nouvelle version de ce {kind_label} qui garde "
        f"EXACTEMENT le même angle, la même offre et la même structure que l'original, "
        f"à l'exception d'UNE SEULE dimension à faire varier : {dimension_label}. "
        f"Ne réécris pas les autres parties — seule {dimension_label} doit changer par "
        f"rapport à l'original ci-dessus. L'objectif est d'isoler l'effet de ce seul "
        f"changement sur la conversion, pas de produire un texte entièrement nouveau."
    )

    copy = _call_claude_for_copy(user_prompt, model)

    return Variant(
        product_id=product.id, kind=kind, framework=reference.detected_framework, copy=copy,
        source_mode=GenerationMode.OPTIMIZE_EXISTING, varied_dimension=vary_dimension,
    )


def generate_variants_from_reference(
    product: Product,
    kind: VariantKind,
    reference: ExistingCopyAnalysis,
    dimensions: list[VaryDimension] | None = None,
    model: str = DEFAULT_MODEL,
) -> list[Variant]:
    """Mode "Optimiser un existant" : une variante par dimension à tester
    (les 4 par défaut : hook, preuve sociale, urgence, CTA)."""
    dimensions = dimensions or [
        VaryDimension.HOOK, VaryDimension.SOCIAL_PROOF, VaryDimension.URGENCY, VaryDimension.CTA,
    ]
    return [
        generate_variant_from_reference(product, kind, reference, dim, model=model)
        for dim in dimensions
    ]

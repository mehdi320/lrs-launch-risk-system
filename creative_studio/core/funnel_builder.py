"""Mode "Funnel Builder" : génère la structure complète d'un funnel
(page de capture/advertorial -> page de vente -> page de confirmation/upsell)
plutôt qu'une page isolée.

Deux appels Claude en séquence :
1. generate_funnel_brief() : UN appel qui fixe l'angle, le ton et la
   promesse partagés par TOUTES les pages du funnel, avant toute rédaction.
2. Un appel _call_claude_for_copy() (le même cœur de génération que les
   modes "Créer depuis zéro" et "Optimiser un existant" dans
   copy_generation.py) par page du funnel, chacun recevant le brief pour
   rester cohérent avec les autres maillons.

Chaque page générée est un Variant standard (core.variants.Variant) — donc
testable A/B, servi et audité via le pipeline existant sans aucune
duplication. Seul FunnelStep (storage/repository.FunnelRepository) ajoute le
lien "cette page appartient à ce funnel, à cette position".
"""

from __future__ import annotations

from creative_studio.core.copy_generation import KIND_LABELS, DEFAULT_MODEL, _call_claude_for_copy
from creative_studio.core.llm_client import build_client, parse_structured_json_response
from creative_studio.core.variants import (
    Framework,
    Funnel,
    FunnelObjective,
    GenerationMode,
    Product,
    Variant,
    VariantKind,
)

__all__ = [
    "FUNNEL_OBJECTIVE_LABELS",
    "FUNNEL_STEP_TEMPLATES",
    "generate_funnel",
    "generate_funnel_brief",
]

# Séquence de types de pages générées selon l'objectif de conversion visé —
# c'est la seule chose qui distingue les 3 objectifs au niveau de
# l'orchestration ; la génération de chaque page individuelle passe toujours
# par le même _call_claude_for_copy.
FUNNEL_STEP_TEMPLATES: dict[FunnelObjective, list[VariantKind]] = {
    FunnelObjective.DIRECT_SALE: [VariantKind.ADVERTORIAL, VariantKind.SALES_PAGE, VariantKind.UPSELL],
    FunnelObjective.EMAIL_CAPTURE: [VariantKind.CAPTURE, VariantKind.SALES_PAGE, VariantKind.CONFIRMATION],
    FunnelObjective.BOOKING: [VariantKind.CAPTURE, VariantKind.BOOKING, VariantKind.CONFIRMATION],
}

FUNNEL_OBJECTIVE_LABELS: dict[FunnelObjective, str] = {
    FunnelObjective.DIRECT_SALE: "Vente directe",
    FunnelObjective.EMAIL_CAPTURE: "Capture email",
    FunnelObjective.BOOKING: "Prise de rendez-vous",
}

_BRIEF_SCHEMA = {
    "type": "object",
    "properties": {
        "angle": {
            "type": "string",
            "description": "L'angle marketing central du funnel, qui doit rester identique sur toutes les pages",
        },
        "tone": {
            "type": "string",
            "description": "Le ton à tenir sur l'ensemble des pages (ex: urgent et direct, rassurant et pédagogique...)",
        },
        "promise": {
            "type": "string",
            "description": "La promesse portée du premier au dernier maillon du funnel",
        },
    },
    "required": ["angle", "tone", "promise"],
    "additionalProperties": False,
}


def generate_funnel_brief(
    product: Product,
    objective: FunnelObjective,
    model: str = DEFAULT_MODEL,
) -> tuple[str, str, str]:
    """Appel Claude dédié qui fixe angle/ton/promesse AVANT la génération des
    pages — c'est ce brief qui garantit que chaque page du funnel porte la
    même promesse plutôt que de le vérifier après coup."""
    client = build_client()
    objective_label = FUNNEL_OBJECTIVE_LABELS[objective]
    user_prompt = (
        f"Produit : {product.name}\n"
        f"Description : {product.description}\n"
        f"Prix : {product.price_cents / 100:.2f} {product.currency}\n"
        f"Cible / audience : {product.audience}\n"
        f"Objectif du funnel : {objective_label}\n\n"
        "Définis l'angle marketing, le ton et la promesse centrale qui devront "
        "rester STRICTEMENT identiques sur toutes les pages du funnel qui seront "
        "rédigées séparément ensuite (page de capture/advertorial, page de vente, "
        "page de confirmation/upsell selon l'objectif) — c'est ce brief qui garantit "
        "la cohérence de bout en bout du funnel."
    )
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": (
                    "Tu es un stratège direct-response qui définit le brief créatif "
                    "d'un funnel de vente avant que chaque page ne soit rédigée."
                ),
            }
        ],
        thinking={"type": "adaptive"},
        output_config={"effort": "high", "format": {"type": "json_schema", "schema": _BRIEF_SCHEMA}},
        messages=[{"role": "user", "content": user_prompt}],
    )
    data = parse_structured_json_response(response)
    return data["angle"], data["tone"], data["promise"]


def _step_user_prompt(
    product: Product,
    kind: VariantKind,
    framework: Framework,
    funnel: Funnel,
    step_order: int,
    total_steps: int,
) -> str:
    kind_label = KIND_LABELS[kind]
    return (
        f"Génère la page {step_order}/{total_steps} d'un funnel : un(e) {kind_label}, "
        f"en utilisant le framework {framework.value}.\n\n"
        f"Produit : {product.name}\n"
        f"Description : {product.description}\n"
        f"Prix : {product.price_cents / 100:.2f} {product.currency}\n"
        f"Cible / audience : {product.audience}\n\n"
        f"CONSIGNE DE COHÉRENCE DU FUNNEL (impérative) — reprends exactement :\n"
        f"Angle : {funnel.angle}\n"
        f"Ton : {funnel.tone}\n"
        f"Promesse portée du premier au dernier maillon : {funnel.promise}\n\n"
        f"Cette page est le maillon {step_order} sur {total_steps} du funnel. Garde "
        f"l'angle, le ton et la promesse ci-dessus strictement identiques à ceux des "
        f"autres pages du funnel — seul le rôle de cette page ({kind_label}) doit "
        f"orienter son contenu et son CTA."
    )


def generate_funnel(
    product: Product,
    objective: FunnelObjective,
    framework: Framework = Framework.AIDA,
    model: str = DEFAULT_MODEL,
) -> tuple[Funnel, list[Variant]]:
    """Génère la structure complète d'un funnel : un appel de brief puis un
    appel séquentiel par étape, chaque étape recevant le brief pour rester
    cohérente avec les autres. Les Variant retournés (dans l'ordre des
    étapes) sont des Variant standard, sans aucune particularité de
    persistance ou de diffusion — à créer via VariantRepository comme
    n'importe quelle autre variante, puis à lier via FunnelStep.
    """
    angle, tone, promise = generate_funnel_brief(product, objective, model=model)
    funnel = Funnel(product_id=product.id, objective=objective, angle=angle, tone=tone, promise=promise)

    kinds = FUNNEL_STEP_TEMPLATES[objective]
    variants: list[Variant] = []
    for step_order, kind in enumerate(kinds, start=1):
        user_prompt = _step_user_prompt(product, kind, framework, funnel, step_order, len(kinds))
        copy = _call_claude_for_copy(user_prompt, model)
        variants.append(
            Variant(
                product_id=product.id,
                kind=kind,
                framework=framework,
                copy=copy,
                source_mode=GenerationMode.FUNNEL_BUILDER,
            )
        )
    return funnel, variants

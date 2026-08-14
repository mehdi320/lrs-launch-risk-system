"""Génération de séquences email via Claude, cohérentes avec le copy gagnant
d'une page de vente.

Progression imposée : valeur -> preuve sociale -> urgence -> offre, répartie
sur la longueur demandée (5, 7 ou 14 emails). Sortie structurée pour éviter
tout parsing fragile.
"""

from __future__ import annotations

import json
from typing import Literal

from creative_studio.core.copy_generation import DEFAULT_MODEL
from creative_studio.core.llm_client import GenerationRefused, build_client
from creative_studio.core.variants import EmailSequence, Product, Variant

SequenceLength = Literal[5, 7, 14]

_SEQUENCE_SYSTEM_PROMPT = [
    {
        "type": "text",
        "text": (
            "Tu es un copywriter email direct-response expert en produits digitaux. "
            "Tu écris des séquences email cohérentes avec un angle produit et un copy "
            "de page de vente déjà validé. La séquence suit toujours une progression "
            "de conversion en 4 phases réparties sur les emails : "
            "1) VALEUR (apporter un résultat rapide, construire la confiance), "
            "2) PREUVE SOCIALE (témoignages, résultats d'autres clients, autorité), "
            "3) URGENCE (deadline, rareté réelle, coût de l'inaction), "
            "4) OFFRE (présentation directe de l'offre et du lien de paiement). "
            "Ne jamais mettre uniquement de l'offre dès le premier email. "
            "Réponds uniquement avec le contenu demandé, sans commentaire méta."
        ),
        "cache_control": {"type": "ephemeral"},
    }
]

_SEQUENCE_SCHEMA = {
    "type": "object",
    "properties": {
        "emails": {
            "type": "array",
            "description": "Liste des emails de la séquence, dans l'ordre d'envoi",
            "items": {
                "type": "object",
                "properties": {
                    "day_offset": {
                        "type": "integer",
                        "description": "Jour d'envoi relatif au jour 0 (premier email = 0)",
                    },
                    "goal": {
                        "type": "string",
                        "enum": ["valeur", "preuve_sociale", "urgence", "offre"],
                        "description": "Phase de la progression de conversion couverte par cet email",
                    },
                    "subject": {"type": "string", "description": "Objet de l'email"},
                    "body": {"type": "string", "description": "Corps de l'email complet"},
                },
                "required": ["day_offset", "goal", "subject", "body"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["emails"],
    "additionalProperties": False,
}


def generate_email_sequence(
    product: Product,
    angle: str,
    length: SequenceLength = 7,
    winning_variant: Variant | None = None,
    model: str = DEFAULT_MODEL,
) -> EmailSequence:
    """Génère une séquence de `length` emails (5, 7 ou 14) pour un produit et un angle donnés.

    `winning_variant`, si fourni, ancre la séquence sur le copy de la page de
    vente gagnante d'un test A/B (cohérence de message, mêmes preuves/CTA).
    """
    if length not in (5, 7, 14):
        raise ValueError("length doit être 5, 7 ou 14")

    client = build_client()

    context_lines = [
        f"Produit : {product.name}",
        f"Description : {product.description}",
        f"Prix : {product.price_cents / 100:.2f} {product.currency}",
        f"Cible / audience : {product.audience}",
        f"Angle / idée produit : {angle}",
        f"Longueur de séquence demandée : {length} emails",
    ]
    if winning_variant is not None:
        context_lines.append(
            "Copy de la page de vente gagnante à réutiliser comme référence de ton et de preuves :\n"
            f"- Headline : {winning_variant.copy.headline}\n"
            f"- Hook : {winning_variant.copy.hook}\n"
            f"- CTA : {winning_variant.copy.cta}"
        )

    response = client.messages.create(
        model=model,
        max_tokens=8192,
        system=_SEQUENCE_SYSTEM_PROMPT,
        thinking={"type": "adaptive"},
        output_config={
            "effort": "high",
            "format": {"type": "json_schema", "schema": _SEQUENCE_SCHEMA},
        },
        messages=[{"role": "user", "content": "\n".join(context_lines)}],
    )

    if response.stop_reason == "refusal":
        category = getattr(response.stop_details, "category", None) if response.stop_details else None
        raise GenerationRefused(f"Génération refusée par Claude (catégorie: {category})")

    text_block = next(b for b in response.content if b.type == "text")
    data = json.loads(text_block.text)

    return EmailSequence(
        product_id=product.id,
        angle=angle,
        length=length,
        emails=data["emails"],
    )

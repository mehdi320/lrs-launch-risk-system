"""Résolution de la clé API Anthropic et construction du client Claude,
partagées entre copy_generation.py et email_sequences.py.
"""

from __future__ import annotations

import json
import os

try:
    import anthropic
except ImportError:  # SDK optionnel tant que le module n'est pas utilisé
    anthropic = None


def get_anthropic_api_key() -> str:
    """Résout la clé API Claude — variable d'env d'abord, puis st.secrets.

    Miroir du pattern get_api_key() existant dans app.py pour OPENAI_API_KEY.
    """
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if key.startswith("sk-ant-"):
        return key
    try:
        import streamlit as st

        key = st.secrets.get("ANTHROPIC_API_KEY", "")
        if key.startswith("sk-ant-"):
            return key
    except Exception:
        pass
    return ""


def build_client() -> "anthropic.Anthropic":
    if anthropic is None:
        raise RuntimeError("Le SDK 'anthropic' n'est pas installé (pip install anthropic).")
    api_key = get_anthropic_api_key()
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY manquant (voir .env.example).")
    return anthropic.Anthropic(api_key=api_key)


class GenerationRefused(RuntimeError):
    """Levée quand Claude refuse la génération (stop_reason == 'refusal')."""


def parse_structured_json_response(response) -> dict:
    """Valide stop_reason puis parse le premier bloc texte comme JSON.

    Centralise la gestion des cas d'échec d'une réponse à sortie structurée :
    refus (stop_reason == 'refusal'), troncature (stop_reason == 'max_tokens',
    la réponse JSON est alors incomplète), et tout JSON malformé/absent —
    pour ne jamais laisser une exception brute (StopIteration,
    JSONDecodeError) remonter jusqu'à l'UI.
    """
    if response.stop_reason == "refusal":
        category = getattr(response.stop_details, "category", None) if response.stop_details else None
        raise GenerationRefused(f"Génération refusée par Claude (catégorie: {category})")

    if response.stop_reason == "max_tokens":
        raise RuntimeError(
            "Réponse tronquée (limite de tokens atteinte) — la génération est incomplète. "
            "Réessayez, ou réduisez la longueur demandée."
        )

    text_block = next((b for b in response.content if b.type == "text"), None)
    if text_block is None:
        raise RuntimeError(f"Réponse inattendue de Claude (stop_reason={response.stop_reason!r}, aucun texte).")

    try:
        return json.loads(text_block.text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Réponse JSON invalide reçue de Claude : {exc}") from exc

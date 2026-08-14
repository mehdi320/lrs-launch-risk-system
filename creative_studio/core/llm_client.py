"""Résolution de la clé API Anthropic et construction du client Claude,
partagées entre copy_generation.py et email_sequences.py.
"""

from __future__ import annotations

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

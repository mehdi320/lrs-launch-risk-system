"""Éléments de conversion modulaires (timer, réduction limitée, stock
restant) injectables dans une page du Funnel Builder.

Ne passent jamais par core.copy_generation._call_claude_for_copy : ce sont
des composants indépendants du moteur de copy, gérés uniquement par la
couche de rendu — serving/templates.py pour la page servie en direct (avec
un décompte JS live pour les types datés), core/pdf_export.py pour l'export
PDF (forcément statique). render_element_text() est le SEUL point qui
transforme la config d'un élément en texte ; les deux couches de rendu
l'utilisent, aucune n'improvise sa propre logique de formatage.

Architecture volontairement extensible : storage/db.py ne met AUCUN CHECK
sur funnel_step_elements.element_type (contrairement au reste du schéma) —
ajouter un nouveau type ("badge de garantie", "preuve sociale dynamique",
...) ne demande qu'une nouvelle config + une entrée dans _RENDERERS
ci-dessous, jamais de migration.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable

__all__ = [
    "CountdownTimerConfig",
    "ElementType",
    "ELEMENT_TYPE_LABELS",
    "LimitedDiscountConfig",
    "StockCounterConfig",
    "TIME_BASED_ELEMENT_TYPES",
    "countdown_target_iso",
    "render_element_text",
]


class ElementType(str, Enum):
    COUNTDOWN_TIMER = "countdown_timer"
    LIMITED_DISCOUNT = "limited_discount"
    STOCK_COUNTER = "stock_counter"


@dataclass
class CountdownTimerConfig:
    end_at: str  # ISO 8601, ex: "2026-08-20T23:59:00+00:00"
    label: str = "Offre expire dans"


@dataclass
class LimitedDiscountConfig:
    original_price_cents: int
    discounted_price_cents: int
    expires_at: str  # ISO 8601
    currency: str = "EUR"


@dataclass
class StockCounterConfig:
    remaining: int  # saisi manuellement — jamais généré/estimé automatiquement
    label: str = "places restantes"


ELEMENT_CONFIG_TYPES: dict[ElementType, type] = {
    ElementType.COUNTDOWN_TIMER: CountdownTimerConfig,
    ElementType.LIMITED_DISCOUNT: LimitedDiscountConfig,
    ElementType.STOCK_COUNTER: StockCounterConfig,
}

ELEMENT_TYPE_LABELS: dict[ElementType, str] = {
    ElementType.COUNTDOWN_TIMER: "Compte à rebours",
    ElementType.LIMITED_DISCOUNT: "Réduction limitée dans le temps",
    ElementType.STOCK_COUNTER: "Compteur de stock / places restantes",
}

# Types dont le rendu HTML live peut être animé par le petit script JS de
# serving/templates.py (décompte en temps réel) — les autres restent du
# texte statique partout, comme dans le PDF.
TIME_BASED_ELEMENT_TYPES = {ElementType.COUNTDOWN_TIMER, ElementType.LIMITED_DISCOUNT}


def _format_dt(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%d/%m/%Y à %H:%M")
    except (ValueError, TypeError):
        return iso


def _render_countdown_timer(config: dict[str, Any]) -> str:
    c = CountdownTimerConfig(**config)
    return f"⏳ {c.label} : {_format_dt(c.end_at)}"


def _render_limited_discount(config: dict[str, Any]) -> str:
    c = LimitedDiscountConfig(**config)
    original = f"{c.original_price_cents / 100:.2f} {c.currency}"
    discounted = f"{c.discounted_price_cents / 100:.2f} {c.currency}"
    return f"💥 Prix barré {original} → {discounted} — offre valable jusqu'à : {_format_dt(c.expires_at)}"


def _render_stock_counter(config: dict[str, Any]) -> str:
    c = StockCounterConfig(**config)
    return f"🔥 Plus que {c.remaining} {c.label}"


_RENDERERS: dict[ElementType, Callable[[dict[str, Any]], str]] = {
    ElementType.COUNTDOWN_TIMER: _render_countdown_timer,
    ElementType.LIMITED_DISCOUNT: _render_limited_discount,
    ElementType.STOCK_COUNTER: _render_stock_counter,
}


def render_element_text(element_type: str, config: dict[str, Any]) -> str:
    """Représentation textuelle d'un élément — utilisée telle quelle par
    l'export PDF, et comme contenu initial/fallback par le rendu HTML live
    (qui peut en plus l'animer via JS pour les types datés, voir
    countdown_target_iso). Un type inconnu (ex: base migrée depuis une
    version future) est ignoré silencieusement plutôt que de casser le
    rendu de toute la page.
    """
    try:
        element = ElementType(element_type)
    except ValueError:
        return ""
    renderer = _RENDERERS.get(element)
    return renderer(config) if renderer else ""


def countdown_target_iso(element_type: str, config: dict[str, Any]) -> str | None:
    """Extrait la date cible (ISO 8601) d'un élément daté, pour que le rendu
    HTML live puisse l'animer en JS — None si le type n'est pas daté."""
    try:
        element = ElementType(element_type)
    except ValueError:
        return None
    if element == ElementType.COUNTDOWN_TIMER:
        return config.get("end_at")
    if element == ElementType.LIMITED_DISCOUNT:
        return config.get("expires_at")
    return None

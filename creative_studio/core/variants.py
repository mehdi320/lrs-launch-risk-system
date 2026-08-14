"""Modèles de données du cœur métier (Product, Variant, ABTest, Event, ...).

Ces dataclasses ne dépendent ni de Streamlit ni de SQLite — c'est la
frontière "core" qui doit rester testable et portable telle quelle
vers un futur backend multi-tenant (V2).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Framework(str, Enum):
    AIDA = "AIDA"
    PAS = "PAS"
    HORMOZI = "hormozi"


class VariantKind(str, Enum):
    ADVERTORIAL = "advertorial"
    SALES_PAGE = "sales_page"


class VariantStatus(str, Enum):
    DRAFT = "draft"
    TESTING = "testing"
    ARCHIVED = "archived"


class TestStatus(str, Enum):
    RUNNING = "running"
    CONCLUDED = "concluded"
    PAUSED = "paused"


class EventType(str, Enum):
    VIEW = "view"
    CLICK_TO_PAYMENT = "click_to_payment"
    PURCHASE = "purchase"


@dataclass
class Product:
    name: str
    description: str
    price_cents: int
    stripe_payment_link: str
    audience: str
    currency: str = "EUR"
    tenant_id: str = "local"
    id: str = field(default_factory=lambda: new_id("prod"))
    created_at: str = field(default_factory=utcnow_iso)


@dataclass
class CopyBlock:
    """Contenu structuré d'une variante — c'est le schéma attendu de Claude."""
    headline: str
    hook: str
    body_sections: list[str]
    cta: str


@dataclass
class Variant:
    product_id: str
    kind: VariantKind
    framework: Framework
    copy: CopyBlock
    tenant_id: str = "local"
    id: str = field(default_factory=lambda: new_id("var"))
    lrs_score: int | None = None
    status: VariantStatus = VariantStatus.DRAFT
    created_at: str = field(default_factory=utcnow_iso)


@dataclass
class ABTest:
    product_id: str
    name: str
    variant_ids: list[str]
    tenant_id: str = "local"
    id: str = field(default_factory=lambda: new_id("test"))
    status: TestStatus = TestStatus.RUNNING
    winner_variant_id: str | None = None
    created_at: str = field(default_factory=utcnow_iso)
    concluded_at: str | None = None


@dataclass
class Event:
    test_id: str
    variant_id: str
    visitor_id: str
    event_type: EventType
    tenant_id: str = "local"
    amount_cents: int | None = None
    ts: str = field(default_factory=utcnow_iso)


@dataclass
class TestResult:
    test_id: str
    variant_id: str
    exposures: int
    conversions: int
    conversion_rate: float
    p_value: float | None
    is_significant: bool
    is_winner: bool
    computed_at: str = field(default_factory=utcnow_iso)


@dataclass
class EmailSequence:
    product_id: str
    angle: str
    length: int  # 5, 7 ou 14
    emails: list[dict]  # [{subject, body, day_offset, goal}, ...]
    tenant_id: str = "local"
    id: str = field(default_factory=lambda: new_id("seq"))
    created_at: str = field(default_factory=utcnow_iso)

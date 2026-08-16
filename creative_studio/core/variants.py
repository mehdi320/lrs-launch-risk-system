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
    CAPTURE = "capture"  # page de capture email / prise de RDV — 1er maillon d'un funnel
    BOOKING = "booking"  # page de prise de rendez-vous
    CONFIRMATION = "confirmation"  # page de confirmation / merci
    UPSELL = "upsell"  # offre complémentaire proposée après l'achat/la conversion principale


class VariantStatus(str, Enum):
    DRAFT = "draft"
    TESTING = "testing"
    ARCHIVED = "archived"
    KILLED = "killed"  # coupée automatiquement par le garde-fou de budget


class TestStatus(str, Enum):
    RUNNING = "running"
    CONCLUDED = "concluded"
    PAUSED = "paused"


class ConclusionReason(str, Enum):
    STATISTICAL_SIGNIFICANCE = "statistical_significance"
    BUDGET_STOP_LOSS = "budget_stop_loss"  # une seule variante active restante après coupes budget


class EventType(str, Enum):
    VIEW = "view"
    CLICK_TO_PAYMENT = "click_to_payment"
    PURCHASE = "purchase"


class GenerationMode(str, Enum):
    """D'où vient une variante : générée librement, dérivée d'un
    advertorial/page de vente existant en ne faisant varier qu'un paramètre,
    ou générée comme maillon d'un funnel multi-pages cohérent."""
    FROM_SCRATCH = "from_scratch"
    OPTIMIZE_EXISTING = "optimize_existing"
    FUNNEL_BUILDER = "funnel_builder"


class FunnelObjective(str, Enum):
    """Objectif de conversion visé par un funnel généré via Funnel Builder —
    détermine la séquence de types de pages générées (voir
    core.funnel_builder.FUNNEL_STEP_TEMPLATES)."""
    DIRECT_SALE = "direct_sale"
    EMAIL_CAPTURE = "email_capture"
    BOOKING = "booking"


class VaryDimension(str, Enum):
    """Le seul paramètre autorisé à changer par rapport à la référence
    d'origine, en mode Optimisation — pour isoler ce qui améliore la
    conversion plutôt que de réécrire tout le copy à chaque variante."""
    HOOK = "hook"
    SOCIAL_PROOF = "social_proof"
    URGENCY = "urgency"
    CTA = "cta"


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
    source_mode: GenerationMode = GenerationMode.FROM_SCRATCH
    varied_dimension: VaryDimension | None = None
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
    killed_variant_ids: list[str] = field(default_factory=list)
    conclusion_reason: ConclusionReason | None = None
    created_at: str = field(default_factory=utcnow_iso)
    concluded_at: str | None = None

    @property
    def active_variant_ids(self) -> list[str]:
        """Variantes encore éligibles au trafic (ni coupées budget, ni exclues)."""
        killed = set(self.killed_variant_ids)
        return [vid for vid in self.variant_ids if vid not in killed]


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
    alpha_used: float
    n_looks: int
    computed_at: str = field(default_factory=utcnow_iso)


class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"


class MediaSourceType(str, Enum):
    """D'où vient le fichier référencé par FunnelStepMedia.location : un
    upload stocké sur disque local (storage.media), ou une URL externe déjà
    hébergée ailleurs — jamais le binaire lui-même en base."""
    UPLOAD = "upload"
    URL = "url"


class MediaPlacement(str, Enum):
    """Où le média est injecté dans la page générée."""
    HERO = "hero"  # en tête de page
    PROOF = "proof"  # section preuve sociale
    DEMO = "demo"  # démonstration produit


@dataclass
class Funnel:
    """Le brief de cohérence partagé par toutes les pages d'un funnel généré
    via Funnel Builder — angle, ton et promesse fixés UNE fois avant de
    générer les pages, pour que chaque maillon reste aligné avec les autres
    sans avoir à reconstruire cette cohérence a posteriori."""
    product_id: str
    objective: FunnelObjective
    angle: str
    tone: str
    promise: str
    tenant_id: str = "local"
    id: str = field(default_factory=lambda: new_id("funnel"))
    # Lien PDF ou texte utilisé comme base/angle de référence (mode "input par
    # PDF gagnant"), None si le funnel a été construit sans référence.
    source_reference: str | None = None
    created_at: str = field(default_factory=utcnow_iso)


@dataclass
class FunnelStep:
    """Un maillon d'un funnel : pointe vers un Variant standard (même table,
    même pipeline de génération et de test A/B que les autres modes) —
    step_order fixe l'ordre d'affichage/de parcours du funnel."""
    funnel_id: str
    variant_id: str
    step_order: int
    tenant_id: str = "local"
    id: str = field(default_factory=lambda: new_id("fstep"))
    created_at: str = field(default_factory=utcnow_iso)


@dataclass
class FunnelStepMedia:
    """Une photo ou vidéo attachée à un maillon de funnel — le système ne la
    génère pas, il l'intègre à l'emplacement pertinent (placement) dans la
    page rendue/exportée. `location` est soit un nom de fichier généré sous
    storage.media.MEDIA_DIR (source_type=UPLOAD), soit une URL externe
    (source_type=URL) — jamais le binaire lui-même en base."""
    step_id: str
    media_type: MediaType
    source_type: MediaSourceType
    location: str
    placement: MediaPlacement = MediaPlacement.HERO
    tenant_id: str = "local"
    id: str = field(default_factory=lambda: new_id("media"))
    created_at: str = field(default_factory=utcnow_iso)


@dataclass
class FunnelStepElement:
    """Un élément de conversion modulaire (timer, réduction limitée, stock
    restant, ...) activable par page — ne passe jamais par
    core.copy_generation._call_claude_for_copy, uniquement par la couche de
    rendu (voir core.funnel_elements.render_element_text). `element_type` est
    une chaîne libre (pas un Enum ici, pas de CHECK en base) : ajouter un
    nouveau type ne demande qu'une nouvelle config + un nouveau renderer
    dans core.funnel_elements, jamais de migration de schéma."""
    step_id: str
    element_type: str
    config: dict
    enabled: bool = True
    tenant_id: str = "local"
    id: str = field(default_factory=lambda: new_id("elem"))
    created_at: str = field(default_factory=utcnow_iso)


@dataclass
class EmailSequence:
    product_id: str
    angle: str
    length: int  # 5, 7 ou 14
    emails: list[dict]  # [{subject, body, day_offset, goal}, ...]
    tenant_id: str = "local"
    id: str = field(default_factory=lambda: new_id("seq"))
    created_at: str = field(default_factory=utcnow_iso)

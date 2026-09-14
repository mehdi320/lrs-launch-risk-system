"""Serveur MCP exposant le module Creative Studio de LRS.

Quatre outils :
- get_test_status(test_id)      : statut d'un test A/B (lecture seule)
- list_variants(test_id)        : variantes d'un test + leurs métriques live
- trigger_generation(mode, ...) : lance une génération (from scratch / optimisation)
- get_budget_priority(test_id?) : priorisation budget (core.prioritization)

Ce serveur ne fait qu'appeler les fonctions déjà existantes de
creative_studio.core / creative_studio.storage — aucune logique métier
n'est dupliquée ici. Il n'est ni démarré automatiquement, ni enregistré
dans une configuration Claude Desktop par ce dépôt : voir README.md pour
le connecter manuellement quand tu es prêt.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from creative_studio.core.copy_generation import (
    GenerationRefused,
    generate_variants,
    generate_variants_from_reference,
)
from creative_studio.core.prioritization import rank_variants_for_budget
from creative_studio.core.reference_extraction import analyze_existing_copy
from creative_studio.core.stats import VariantStats
from creative_studio.core.variants import (
    Framework,
    GenerationMode,
    Product,
    TestStatus,
    VariantKind,
    VaryDimension,
)
from creative_studio.storage.db import init_db
from creative_studio.storage.repository import (
    ABTestRepository,
    EventRepository,
    ProductRepository,
    TestResultRepository,
    VariantRepository,
)
from mcp_server.config import load_config

_config = load_config()

mcp = FastMCP(
    "lrs-creative-studio",
    host=_config.host,
    port=_config.port,
    instructions=(
        "Outils de pilotage du module Creative Studio de LRS (génération de "
        "créatifs, tests A/B, priorisation budget). Toutes les opérations "
        "portent sur la base SQLite locale du module (.lrs_creative_studio.db)."
    ),
)

_products = ProductRepository()
_variants = VariantRepository()
_tests = ABTestRepository()
_events = EventRepository()
_test_results = TestResultRepository()

init_db()


# ── Helpers internes (pas des outils MCP) ──────────────────────────────

def _variant_to_dict(v, live_stats: VariantStats | None = None) -> dict[str, Any]:
    d = {
        "id": v.id,
        "product_id": v.product_id,
        "kind": v.kind.value,
        "framework": v.framework.value,
        "status": v.status.value,
        "source_mode": v.source_mode.value,
        "varied_dimension": v.varied_dimension.value if v.varied_dimension else None,
        "lrs_score": v.lrs_score,
        "headline": v.copy.headline,
        "hook": v.copy.hook,
        "cta": v.copy.cta,
        "created_at": v.created_at,
    }
    if live_stats is not None:
        d["exposures"] = live_stats.exposures
        d["conversions"] = live_stats.conversions
        d["conversion_rate"] = round(live_stats.conversion_rate, 4)
    return d


def _live_stats_for_test(test_id: str) -> dict[str, VariantStats]:
    exposures = _events.counts_by_variant(test_id, "view")
    conversions = _events.counts_by_variant(test_id, "purchase")
    variant_ids = set(exposures) | set(conversions)
    test = _tests.get(test_id)
    if test:
        variant_ids |= set(test.variant_ids)
    return {
        vid: VariantStats(
            variant_id=vid,
            exposures=exposures.get(vid, 0),
            conversions=conversions.get(vid, 0),
        )
        for vid in variant_ids
    }


def _resolve_product(input_data: dict[str, Any]) -> Product:
    """Résout le produit cible depuis input_data : soit un product_id
    existant, soit les champs pour en créer un nouveau à la volée."""
    product_id = input_data.get("product_id")
    if product_id:
        product = _products.get(product_id)
        if product is None:
            raise ValueError(f"product_id introuvable : {product_id}")
        return product

    required = ["product_name", "product_description", "price_cents", "stripe_payment_link", "audience"]
    missing = [k for k in required if not input_data.get(k)]
    if missing:
        raise ValueError(
            "Ni product_id valide, ni tous les champs requis pour créer un produit : "
            f"champs manquants = {missing}. "
            "Fournis soit 'product_id' (produit déjà créé), soit tous les champs : "
            f"{required} (+ 'currency' optionnel, EUR par défaut)."
        )
    return _products.create(
        Product(
            name=input_data["product_name"],
            description=input_data["product_description"],
            price_cents=int(input_data["price_cents"]),
            currency=input_data.get("currency", "EUR"),
            stripe_payment_link=input_data["stripe_payment_link"],
            audience=input_data["audience"],
        )
    )


def _resolve_kind(input_data: dict[str, Any]) -> VariantKind:
    raw = input_data.get("kind", "sales_page")
    try:
        return VariantKind(raw)
    except ValueError:
        raise ValueError(f"kind invalide : {raw!r} (attendu : 'sales_page' ou 'advertorial')") from None


# ── Outils MCP ──────────────────────────────────────────────────────────

@mcp.tool()
def get_test_status(test_id: str) -> dict[str, Any]:
    """Statut d'un test A/B en cours : métadonnées (statut, gagnant, raison
    de conclusion, variantes coupées/actives) + compteurs d'expositions et
    conversions à jour pour chaque variante.

    Lecture seule et sans coût statistique : ne relance PAS le calcul de
    significativité (ce qui compterait comme une consultation supplémentaire
    au sens de la correction de peeking) — le dernier verdict de
    significativité déjà calculé est renvoyé tel quel, avec sa date de
    calcul, pour que l'appelant sache s'il est à jour ou non.
    """
    test = _tests.get(test_id)
    if test is None:
        raise ValueError(f"Test introuvable : {test_id}")

    live_stats = _live_stats_for_test(test_id)
    live_by_variant = {
        vid: {
            "exposures": s.exposures,
            "conversions": s.conversions,
            "conversion_rate": round(s.conversion_rate, 4),
        }
        for vid, s in live_stats.items()
    }

    last_results = _test_results.latest_for_test(test_id)
    last_significance = (
        {
            "computed_at": last_results[0].computed_at,
            "n_looks": last_results[0].n_looks,
            "alpha_used": last_results[0].alpha_used,
            "results": [
                {
                    "variant_id": r.variant_id,
                    "p_value": r.p_value,
                    "is_significant": r.is_significant,
                    "is_winner": r.is_winner,
                }
                for r in last_results
            ],
        }
        if last_results
        else None
    )

    return {
        "test_id": test.id,
        "name": test.name,
        "product_id": test.product_id,
        "status": test.status.value,
        "winner_variant_id": test.winner_variant_id,
        "conclusion_reason": test.conclusion_reason.value if test.conclusion_reason else None,
        "variant_ids": test.variant_ids,
        "active_variant_ids": test.active_variant_ids,
        "killed_variant_ids": test.killed_variant_ids,
        "created_at": test.created_at,
        "concluded_at": test.concluded_at,
        "live_stats_by_variant": live_by_variant,
        "last_significance_snapshot": last_significance,
    }


@mcp.tool()
def list_variants(test_id: str) -> list[dict[str, Any]]:
    """Liste les variantes d'un test A/B (actives ET coupées) avec leurs
    métriques live (expositions, conversions, taux de conversion) et leur
    copy (headline, hook, CTA)."""
    test = _tests.get(test_id)
    if test is None:
        raise ValueError(f"Test introuvable : {test_id}")

    live_stats = _live_stats_for_test(test_id)
    result = []
    for vid in test.variant_ids:
        variant = _variants.get(vid)
        if variant is None:
            continue
        entry = _variant_to_dict(variant, live_stats.get(vid))
        entry["is_active"] = vid in test.active_variant_ids
        entry["is_killed"] = vid in test.killed_variant_ids
        result.append(entry)
    return result


@mcp.tool()
def trigger_generation(mode: str, input_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Lance une génération de variantes via Claude et les sauvegarde.

    `mode` : "from_scratch" (créer depuis zéro) ou "optimize_existing"
    (optimiser un advertorial/page de vente déjà existant).

    `input_data` (dict) :
    - Produit cible — soit `product_id` (produit déjà créé), soit tous les
      champs pour en créer un : `product_name`, `product_description`,
      `price_cents`, `stripe_payment_link`, `audience` (+ `currency`
      optionnel, EUR par défaut).
    - `kind` (optionnel) : "sales_page" (défaut) ou "advertorial".
    - Mode from_scratch — `frameworks` (optionnel, liste parmi "AIDA",
      "PAS", "hormozi" ; les 3 par défaut).
    - Mode optimize_existing — `reference` (requis : texte collé ou URL de
      la publicité/page existante), `dimensions` (optionnel, liste parmi
      "hook", "social_proof", "urgency", "cta" ; les 4 par défaut).

    Coûte un appel réel à l'API Claude (ANTHROPIC_API_KEY doit être
    configurée dans l'environnement du serveur MCP).
    """
    product = _resolve_product(input_data)
    kind = _resolve_kind(input_data)

    try:
        if mode == GenerationMode.FROM_SCRATCH.value:
            raw_frameworks = input_data.get("frameworks")
            frameworks = [Framework(f) for f in raw_frameworks] if raw_frameworks else None
            new_variants = generate_variants(product, kind, frameworks)

        elif mode == GenerationMode.OPTIMIZE_EXISTING.value:
            reference_input = input_data.get("reference")
            if not reference_input:
                raise ValueError("input_data.reference est requis en mode 'optimize_existing'.")
            raw_dimensions = input_data.get("dimensions")
            dimensions = [VaryDimension(d) for d in raw_dimensions] if raw_dimensions else None
            analysis = analyze_existing_copy(reference_input)
            new_variants = generate_variants_from_reference(product, kind, analysis, dimensions)

        else:
            raise ValueError(
                f"mode invalide : {mode!r} (attendu : 'from_scratch' ou 'optimize_existing')"
            )
    except GenerationRefused as exc:
        raise ValueError(f"Génération refusée par Claude : {exc}") from exc

    for v in new_variants:
        _variants.create(v)

    return [_variant_to_dict(v) for v in new_variants]


@mcp.tool()
def get_budget_priority(test_id: str | None = None) -> list[dict[str, Any]]:
    """Priorisation budget (core.prioritization.rank_variants_for_budget) :
    classe les variantes par priorité décroissante (score LRS x traction
    observée), pour indiquer où allouer plus de trafic de test.

    Sans `test_id` : scanne tous les tests A/B en cours (statut "running")
    de tous les produits et renvoie un classement par test. Avec `test_id` :
    se limite à ce test précis. Seules les variantes actives (non coupées
    par le garde-fou budget) sont classées ; un test sans variante notée
    (score LRS) n'apparaît pas.
    """
    if test_id is not None:
        test = _tests.get(test_id)
        if test is None:
            raise ValueError(f"Test introuvable : {test_id}")
        tests_to_rank = [test]
    else:
        tests_to_rank = [
            t
            for product in _products.list()
            for t in _tests.list_by_product(product.id)
            if t.status == TestStatus.RUNNING
        ]

    output = []
    for test in tests_to_rank:
        active_ids = set(test.active_variant_ids)
        lrs_scores = {}
        for vid in active_ids:
            variant = _variants.get(vid)
            if variant is not None and variant.lrs_score is not None:
                lrs_scores[vid] = variant.lrs_score
        if not lrs_scores:
            continue

        live_stats = _live_stats_for_test(test.id)
        stats = [live_stats[vid] for vid in active_ids if vid in live_stats]
        ranked = rank_variants_for_budget(stats, lrs_scores)

        output.append(
            {
                "test_id": test.id,
                "test_name": test.name,
                "product_id": test.product_id,
                "priorities": [
                    {
                        "variant_id": p.variant_id,
                        "priority_score": round(p.priority_score, 4),
                        "smoothed_conversion_rate": round(p.smoothed_conversion_rate, 4),
                        "lrs_score": p.lrs_score,
                    }
                    for p in ranked
                ],
            }
        )
    return output


def main() -> None:
    mcp.run(transport=_config.transport)


if __name__ == "__main__":
    main()

"""Orchestration : lit les événements réels d'un test A/B, calcule la
significativité (core.stats) et conclut le test automatiquement si un
gagnant statistiquement significatif émerge — sans intervention manuelle.
"""

from __future__ import annotations

from datetime import datetime, timezone

from creative_studio.core.stats import VariantStats, evaluate_test
from creative_studio.core.variants import TestResult
from creative_studio.storage.repository import (
    ABTestRepository,
    EventRepository,
    TestResultRepository,
)


def compute_and_save_results(test_id: str) -> list[TestResult]:
    """Recalcule les résultats d'un test à partir des événements enregistrés,
    sauvegarde un instantané, et conclut le test si un gagnant se dégage.
    """
    tests = ABTestRepository()
    events = EventRepository()
    results_repo = TestResultRepository()

    test = tests.get(test_id)
    if test is None:
        raise ValueError(f"Test introuvable: {test_id}")

    exposures = events.counts_by_variant(test_id, "view")
    conversions = events.counts_by_variant(test_id, "purchase")

    variant_stats = [
        VariantStats(
            variant_id=vid,
            exposures=exposures.get(vid, 0),
            conversions=conversions.get(vid, 0),
        )
        for vid in test.variant_ids
    ]

    results = evaluate_test(variant_stats, test_id=test_id)
    for result in results:
        results_repo.save(result)

    winner = next((r for r in results if r.is_winner), None)
    if winner is not None and test.status.value == "running":
        tests.conclude(test_id, winner.variant_id, datetime.now(timezone.utc).isoformat())

    return results

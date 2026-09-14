"""Orchestration : lit les événements réels d'un test A/B, calcule la
significativité (core.stats, avec correction de peeking) et conclut le
test automatiquement — soit parce qu'un gagnant statistiquement
significatif émerge, soit parce que le garde-fou de budget (core.budget_guard)
a coupé toutes les variantes sauf une — sans intervention manuelle.
"""

from __future__ import annotations

from datetime import datetime, timezone

from creative_studio.core.budget_guard import DEFAULT_KILL_EXPOSURE_THRESHOLD, find_variants_to_kill
from creative_studio.core.stats import SIGNIFICANCE_ALPHA, VariantStats, evaluate_test
from creative_studio.core.variants import ConclusionReason, TestResult, TestStatus, VariantStatus
from creative_studio.storage.repository import (
    ABTestRepository,
    EventRepository,
    TestResultRepository,
    VariantRepository,
)


def compute_and_save_results(
    test_id: str,
    kill_exposure_threshold: int = DEFAULT_KILL_EXPOSURE_THRESHOLD,
) -> list[TestResult]:
    """Recalcule les résultats d'un test à partir des événements enregistrés,
    sauvegarde un instantané, et conclut le test si un gagnant se dégage —
    par significativité statistique ou par épuisement du budget des
    variantes concurrentes.
    """
    tests = ABTestRepository()
    events = EventRepository()
    results_repo = TestResultRepository()

    test = tests.get(test_id)
    if test is None:
        raise ValueError(f"Test introuvable: {test_id}")

    exposures = events.counts_by_variant(test_id, "view")
    conversions = events.counts_by_variant(test_id, "purchase")

    all_stats = {
        vid: VariantStats(variant_id=vid, exposures=exposures.get(vid, 0), conversions=conversions.get(vid, 0))
        for vid in test.variant_ids
    }
    active_ids = set(test.active_variant_ids)
    active_stats = [all_stats[vid] for vid in test.variant_ids if vid in active_ids]

    # n_looks compte CETTE évaluation — la correction de Bonferroni
    # (core.stats.evaluate_test) durcit le seuil de significativité à mesure
    # que ce test est consulté, pour ne pas gonfler le taux de faux positifs.
    n_looks = results_repo.count_prior_looks(test_id) + 1
    results = evaluate_test(active_stats, test_id=test_id, n_looks=n_looks)

    # Lignes "figées" pour les variantes déjà coupées par le garde-fou de
    # budget : conservées pour l'historique/l'affichage, mais exclues de la
    # course au gagnant (elles ne reçoivent plus de trafic, donc leur taux
    # ne peut plus être comparé équitablement aux variantes actives).
    frozen_alpha = SIGNIFICANCE_ALPHA / max(n_looks, 1)
    for vid in test.killed_variant_ids:
        stats = all_stats[vid]
        results.append(
            TestResult(
                test_id=test_id, variant_id=vid, exposures=stats.exposures,
                conversions=stats.conversions, conversion_rate=stats.conversion_rate,
                p_value=None, is_significant=False, is_winner=False,
                alpha_used=frozen_alpha, n_looks=n_looks,
            )
        )

    for result in results:
        results_repo.save(result)

    winner = next((r for r in results if r.is_winner), None)
    if winner is not None and test.status == TestStatus.RUNNING:
        tests.conclude(
            test_id, winner.variant_id, datetime.now(timezone.utc).isoformat(),
            reason=ConclusionReason.STATISTICAL_SIGNIFICANCE,
        )
        return results

    # ── Garde-fou de budget ────────────────────────────────────────────
    # Une variante qui brûle du trafic sans jamais s'imposer après
    # `kill_exposure_threshold` expositions est coupée plutôt que d'attendre
    # indéfiniment une significativité qui ne viendra peut-être jamais.
    if test.status == TestStatus.RUNNING and len(active_stats) >= 2:
        to_kill = find_variants_to_kill(active_stats, kill_exposure_threshold=kill_exposure_threshold)
        if to_kill:
            variants_repo = VariantRepository()
            for decision in to_kill:
                tests.kill_variant(test_id, decision.variant_id)
                variants_repo.update_status(decision.variant_id, VariantStatus.KILLED)

            test = tests.get(test_id)  # relit l'état à jour après les coupes
            remaining_active = test.active_variant_ids
            if len(remaining_active) == 1 and test.status == TestStatus.RUNNING:
                tests.conclude(
                    test_id, remaining_active[0], datetime.now(timezone.utc).isoformat(),
                    reason=ConclusionReason.BUDGET_STOP_LOSS,
                )

    return results

"""Priorisation du budget de test entre variantes.

Combine le score LRS (méthodologie déjà en place dans LRS) et le taux de
conversion observé (lissé pour ne pas sur-réagir à un petit échantillon)
pour indiquer quelles variantes méritent plus de trafic de test — sans
attendre la significativité statistique complète, qui ne sert qu'à
déclarer un gagnant définitif (voir core.stats).
"""

from __future__ import annotations

from dataclasses import dataclass

from creative_studio.core.stats import VariantStats


@dataclass
class BudgetPriority:
    variant_id: str
    smoothed_conversion_rate: float
    lrs_score: int | None
    priority_score: float


def _smoothed_rate(stats: VariantStats) -> float:
    """Lissage de Laplace : évite qu'un 1/1 (100%) écrase un 40/1000 (4%)."""
    return (stats.conversions + 1) / (stats.exposures + 2)


def rank_variants_for_budget(
    variant_stats: list[VariantStats],
    lrs_scores: dict[str, int],
) -> list[BudgetPriority]:
    """Classe les variantes par priorité de budget de test décroissante.

    priorité = taux de conversion lissé x (1 + score_LRS / 20)
    Une variante avec un bon score LRS ET un bon taux observé est priorisée ;
    un score LRS élevé sans traction réelle ne suffit pas à lui seul.
    """
    ranked: list[BudgetPriority] = []
    for stats in variant_stats:
        score = lrs_scores.get(stats.variant_id)
        rate = _smoothed_rate(stats)
        multiplier = 1 + (score / 20) if score is not None else 1.0
        ranked.append(
            BudgetPriority(
                variant_id=stats.variant_id,
                smoothed_conversion_rate=rate,
                lrs_score=score,
                priority_score=rate * multiplier,
            )
        )
    ranked.sort(key=lambda p: p.priority_score, reverse=True)
    return ranked

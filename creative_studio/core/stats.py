"""Moteur de significativité statistique pour les tests A/B.

Approche : test de proportions à deux échantillons (z-test), avec un seuil
de taille d'échantillon minimum avant toute déclaration de gagnant — pour
éviter de conclure sur un échantillon de 3 visiteurs. Le système ne déclare
jamais un gagnant sur la simple comparaison du taux brut.

Garde-fou anti faux positif (peeking) : chaque fois qu'on regarde les
résultats d'un test avant sa fin, c'est une comparaison statistique
supplémentaire — sans correction, le taux de faux positifs réel dérive très
au-dessus des 5% nominaux à mesure que le nombre de consultations augmente
(le classique problème du "repeated significance testing"). `evaluate_test`
applique donc une correction de Bonferroni dynamique : le seuil de
significativité utilisé est `alpha / n_looks`, où `n_looks` est le nombre
total de consultations de CE test (celle-ci incluse). C'est une correction
conservative et simple à auditer plutôt qu'un plan de test séquentiel complet
(alpha-spending / O'Brien-Fleming) — largement suffisante pour un usage
local, et le nombre de looks utilisé est conservé dans TestResult.alpha_used
/ TestResult.n_looks pour audit.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from creative_studio.core.variants import TestResult

# Aucune déclaration de gagnant tant qu'une variante n'a pas au moins ce
# nombre d'expositions (vues) — évite de conclure sur un échantillon de 3 visiteurs.
MIN_SAMPLE_SIZE = 200

# Seuil de significativité nominal (p-value bilatérale) avant correction de
# peeking. Le seuil réellement appliqué est SIGNIFICANCE_ALPHA / n_looks.
SIGNIFICANCE_ALPHA = 0.05


@dataclass
class VariantStats:
    variant_id: str
    exposures: int
    conversions: int

    @property
    def conversion_rate(self) -> float:
        return self.conversions / self.exposures if self.exposures else 0.0


def _std_normal_cdf(z: float) -> float:
    """CDF de la loi normale centrée réduite, sans dépendance à scipy."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def two_proportion_z_test(a: VariantStats, b: VariantStats) -> float | None:
    """Test bilatéral de comparaison de deux proportions. Retourne la p-value,
    ou None si l'échantillon est insuffisant pour un test fiable.
    """
    if a.exposures == 0 or b.exposures == 0:
        return None

    p_pool = (a.conversions + b.conversions) / (a.exposures + b.exposures)
    if p_pool in (0.0, 1.0):
        # Aucune variance (0% ou 100% de conversion des deux côtés) : rien à tester.
        return None

    se = math.sqrt(p_pool * (1 - p_pool) * (1 / a.exposures + 1 / b.exposures))
    if se == 0:
        return None

    z = (a.conversion_rate - b.conversion_rate) / se
    p_value = 2 * (1 - _std_normal_cdf(abs(z)))
    return p_value


def evaluate_test(
    variant_stats: list[VariantStats],
    test_id: str,
    min_sample_size: int = MIN_SAMPLE_SIZE,
    alpha: float = SIGNIFICANCE_ALPHA,
    n_looks: int = 1,
) -> list[TestResult]:
    """Évalue toutes les variantes d'un test et détermine s'il y a un gagnant
    statistiquement significatif.

    Règle : un gagnant n'est déclaré que si (a) toutes les variantes comparées
    ont atteint `min_sample_size` expositions, et (b) la meilleure variante bat
    significativement (p < alpha effectif) TOUTES les autres variantes — pas
    seulement celle avec le taux brut le plus haut face à une seule autre.

    `n_looks` : nombre total de consultations de ce test, CETTE évaluation
    incluse. Le seuil de significativité effectivement utilisé est
    `alpha / n_looks` (correction de Bonferroni) — plus un test est regardé
    souvent avant sa conclusion, plus la barre à franchir pour déclarer un
    gagnant se durcit, ce qui compense l'inflation du taux de faux positifs
    due au peeking répété.
    """
    results: list[TestResult] = []
    if not variant_stats:
        return results

    n_looks = max(n_looks, 1)
    effective_alpha = alpha / n_looks

    ready = all(v.exposures >= min_sample_size for v in variant_stats)
    best = max(variant_stats, key=lambda v: v.conversion_rate)

    winner_id: str | None = None
    if ready and len(variant_stats) >= 2:
        beats_all_others = True
        for other in variant_stats:
            if other.variant_id == best.variant_id:
                continue
            p_value = two_proportion_z_test(best, other)
            if p_value is None or p_value >= effective_alpha:
                beats_all_others = False
                break
        if beats_all_others:
            winner_id = best.variant_id

    for v in variant_stats:
        p_value_vs_best = None
        if v.variant_id != best.variant_id:
            p_value_vs_best = two_proportion_z_test(best, v)
        results.append(
            TestResult(
                test_id=test_id,
                variant_id=v.variant_id,
                exposures=v.exposures,
                conversions=v.conversions,
                conversion_rate=v.conversion_rate,
                p_value=p_value_vs_best,
                is_significant=(p_value_vs_best is not None and p_value_vs_best < effective_alpha),
                is_winner=(v.variant_id == winner_id),
                alpha_used=effective_alpha,
                n_looks=n_looks,
            )
        )
    return results

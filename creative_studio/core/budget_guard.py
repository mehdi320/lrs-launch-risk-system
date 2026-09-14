"""Garde-fou de budget : coupe automatiquement une variante qui accumule
des expositions (impressions) sans jamais s'imposer, plutôt que de
continuer à lui envoyer du trafic indéfiniment en attendant une
significativité qui ne viendra peut-être jamais.

Règle (stop-loss / futility) : une variante non meneuse est coupée dès
qu'elle dépasse `kill_exposure_threshold` expositions ET qu'elle affiche un
taux de conversion strictement inférieur à la variante en tête à ce
moment-là — qu'elle ait déjà "perdu" statistiquement ou qu'elle soit
simplement restée indécise sans jamais se démarquer. La variante en tête
n'est jamais coupée, même si le test n'a pas encore atteint la
significativité globale.
"""

from __future__ import annotations

from dataclasses import dataclass

from creative_studio.core.stats import VariantStats

# Nombre d'expositions au-delà duquel une variante à la traîne est coupée
# si elle ne s'est toujours pas imposée — évite de continuer à financer du
# trafic de test sur une variante qui ne convertit manifestement pas mieux.
DEFAULT_KILL_EXPOSURE_THRESHOLD = 2000


@dataclass
class KillDecision:
    variant_id: str
    exposures: int
    conversion_rate: float
    reason: str


def find_variants_to_kill(
    variant_stats: list[VariantStats],
    kill_exposure_threshold: int = DEFAULT_KILL_EXPOSURE_THRESHOLD,
) -> list[KillDecision]:
    """Identifie les variantes à couper parmi celles encore actives.

    `variant_stats` ne doit contenir que les variantes actuellement actives
    (déjà coupées exclues en amont) — la variante avec le meilleur taux de
    conversion parmi elles n'est jamais retournée, quel que soit son nombre
    d'expositions.
    """
    if len(variant_stats) < 2:
        return []

    best = max(variant_stats, key=lambda v: v.conversion_rate)

    decisions = []
    for v in variant_stats:
        if v.variant_id == best.variant_id:
            continue
        if v.exposures >= kill_exposure_threshold and v.conversion_rate < best.conversion_rate:
            decisions.append(
                KillDecision(
                    variant_id=v.variant_id,
                    exposures=v.exposures,
                    conversion_rate=v.conversion_rate,
                    reason=(
                        f"{v.exposures} expositions sans dépasser la variante en tête "
                        f"({v.conversion_rate * 100:.2f}% vs {best.conversion_rate * 100:.2f}%)"
                    ),
                )
            )
    return decisions

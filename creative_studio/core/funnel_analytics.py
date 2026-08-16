"""Analytics de funnel par étape — étend le tracking d'événements déjà en
place (vues, clics, achats, désormais formulaires) pour calculer le taux de
passage d'une étape du funnel à la suivante, pas seulement la conversion
finale.

Ne recalcule rien de nouveau : agrège les événements déjà enregistrés par
serving/app.py (mêmes tables `events`/`ab_tests`), keyé par le test A/B qui
sert réellement le trafic de chaque étape (ABTestRepository.find_by_variant).
Un visiteur "passe" d'une étape à la suivante quand il génère un VIEW sur
l'étape suivante (les CTA de funnel étant chaînés, voir
serving/app.py::_resolve_next_url) — aucun nouvel événement dédié n'est
nécessaire pour ce signal ; FORM_SUBMIT ne sert qu'à mesurer la complétion
du formulaire d'une étape de capture, en plus du passage à l'étape suivante.
"""

from __future__ import annotations

from dataclasses import dataclass

from creative_studio.storage.repository import (
    ABTestRepository,
    EventRepository,
    FormSubmissionRepository,
    FunnelRepository,
)

__all__ = ["FunnelStepStats", "compute_funnel_dropoff"]


@dataclass
class FunnelStepStats:
    step_order: int
    variant_id: str
    test_id: str | None  # None si cette étape n'a pas encore de test A/B actif
    views: int
    form_submits: int
    purchases: int
    dropoff_rate_from_previous: float | None  # None pour la première étape


def compute_funnel_dropoff(funnel_id: str) -> list[FunnelStepStats]:
    """Vues, soumissions de formulaire et achats par étape (dans l'ordre du
    funnel), plus le taux de passage depuis l'étape précédente
    (views(N) / views(N-1)). Une étape sans test A/B associé renvoie des
    compteurs à zéro plutôt que d'échouer — le funnel peut être partiellement
    testé."""
    funnels = FunnelRepository()
    tests = ABTestRepository()
    events = EventRepository()
    form_submissions = FormSubmissionRepository()

    steps = funnels.list_steps(funnel_id)
    stats: list[FunnelStepStats] = []
    previous_views: int | None = None

    for step in steps:
        test = tests.find_by_variant(step.variant_id)
        if test is None:
            stats.append(
                FunnelStepStats(
                    step_order=step.step_order, variant_id=step.variant_id, test_id=None,
                    views=0, form_submits=0, purchases=0, dropoff_rate_from_previous=None,
                )
            )
            previous_views = None
            continue

        views = sum(events.counts_by_variant(test.id, "view").values())
        submits = sum(form_submissions.count_by_variant(test.id).values())
        purchases = sum(events.counts_by_variant(test.id, "purchase").values())

        dropoff_rate = (views / previous_views) if previous_views else None
        stats.append(
            FunnelStepStats(
                step_order=step.step_order, variant_id=step.variant_id, test_id=test.id,
                views=views, form_submits=submits, purchases=purchases,
                dropoff_rate_from_previous=dropoff_rate,
            )
        )
        previous_views = views

    return stats

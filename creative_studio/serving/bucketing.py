"""Assignation stable visiteur -> variante pour un test A/B.

L'assignation initiale est déterministe (hash du visitor_id) pour que deux
processus concurrents qui n'ont pas encore vu la table `assignments`
convergent quand même vers le même choix ; la table reste la source de
vérité pour toutes les visites suivantes (via AssignmentRepository.get_or_assign).
"""

from __future__ import annotations

import hashlib

from creative_studio.core.variants import ABTest, TestStatus


def pick_variant_for_new_visitor(test: ABTest, visitor_id: str) -> str:
    """Répartition uniforme et déterministe sur les variantes encore actives.

    Une fois le test conclu (significativité statistique ou stop-loss
    budget), tout nouveau visiteur reçoit directement la variante gagnante —
    inutile de continuer à envoyer du trafic vers les variantes perdantes.
    Tant que le test tourne, les variantes coupées par le garde-fou de
    budget (core.budget_guard) sont exclues de la répartition.
    """
    if test.status == TestStatus.CONCLUDED and test.winner_variant_id:
        return test.winner_variant_id
    active_ids = test.active_variant_ids
    if not active_ids:
        raise ValueError(f"Le test {test.id} n'a aucune variante active.")
    digest = hashlib.sha256(f"{test.id}:{visitor_id}".encode("utf-8")).hexdigest()
    bucket = int(digest, 16) % len(active_ids)
    return sorted(active_ids)[bucket]

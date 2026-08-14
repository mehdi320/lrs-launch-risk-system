"""Assignation stable visiteur -> variante pour un test A/B.

L'assignation initiale est déterministe (hash du visitor_id) pour que deux
processus concurrents qui n'ont pas encore vu la table `assignments`
convergent quand même vers le même choix ; la table reste la source de
vérité pour toutes les visites suivantes (via AssignmentRepository.get_or_assign).
"""

from __future__ import annotations

import hashlib

from creative_studio.core.variants import ABTest


def pick_variant_for_new_visitor(test: ABTest, visitor_id: str) -> str:
    """Répartition uniforme et déterministe sur les variantes actives du test."""
    if not test.variant_ids:
        raise ValueError(f"Le test {test.id} n'a aucune variante.")
    digest = hashlib.sha256(f"{test.id}:{visitor_id}".encode("utf-8")).hexdigest()
    bucket = int(digest, 16) % len(test.variant_ids)
    return sorted(test.variant_ids)[bucket]

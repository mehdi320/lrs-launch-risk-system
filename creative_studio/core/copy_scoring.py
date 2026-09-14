"""Score de structure copywriting — estimation heuristique, PAS une
prédiction de taux de conversion réel.

Aucun appel Claude ici, volontairement : le seul moteur qui mesure une
vraie conversion est le pipeline A/B (core/stats.py, core/test_evaluation.py)
une fois du trafic réel collecté. Ce module ne fait que de l'analyse de
texte déterministe (regex, comptages, formule de lisibilité) sur des
critères structurels objectifs — présence d'éléments, pas jugement de leur
qualité ou de leur véracité. C'est reproductible et auditable, contrairement
à un deuxième avis d'IA qui se ferait passer pour une mesure.

Usage prévu : aider à PRIORISER quelles variantes lancer en test A/B en
premier (les mieux notées structurellement ont statistiquement plus de
chances de bien performer), jamais à annoncer un résultat business. Chaque
affichage de ce score doit être accompagné de SCORE_DISCLAIMER.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

from creative_studio.core.reference_extraction import ExistingCopyAnalysis
from creative_studio.core.variants import CopyBlock, FunnelStepElement

__all__ = [
    "SCORE_DISCLAIMER",
    "CopyScore",
    "CopyScoreComparison",
    "CriterionScore",
    "ScorableCopy",
    "compare_scores",
    "compute_copy_score",
    "scorable_from_copy_block",
    "scorable_from_reference",
]

SCORE_DISCLAIMER = (
    "Estimation structurelle du copy — pas une prédiction de taux de conversion réel. "
    "Seul un test A/B avec du trafic réel (onglet Tests A/B) mesure une vraie conversion."
)

# Pondération des 6 critères — somme = 100. Promesse et preuve pèsent le
# plus lourd (leviers à plus fort impact en direct-response) ; lisibilité
# le moins (signal de confort, pas de conversion en soi).
_MAX_POINTS = {
    "promise_clarity": 20,
    "proof": 20,
    "audience_clarity": 15,
    "conversion_elements": 20,
    "readability": 10,
    "cta_clarity": 15,
}


@dataclass
class ScorableCopy:
    """Représentation minimale nécessaire au scoring — commune à une
    variante générée (CopyBlock) et à un texte de référence collé/PDF."""
    promise_text: str  # titre + accroche
    body_text: str  # corps complet
    cta_text: str


@dataclass
class CriterionScore:
    slug: str
    label: str
    score: int
    max_points: int
    detail: str


@dataclass
class CopyScore:
    total: int
    criteria: list[CriterionScore] = field(default_factory=list)
    computed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class CopyScoreComparison:
    before: CopyScore
    after: CopyScore
    delta_total: int
    delta_by_criterion: dict[str, int]


def scorable_from_copy_block(copy: CopyBlock) -> ScorableCopy:
    return ScorableCopy(
        promise_text=f"{copy.headline} {copy.hook}",
        body_text="\n".join(copy.body_sections),
        cta_text=copy.cta,
    )


def scorable_from_reference(analysis: ExistingCopyAnalysis, raw_text: str) -> ScorableCopy:
    """Construit le "avant" à partir de ce que analyze_existing_copy() a déjà
    extrait (hook, CTA — la référence n'a pas de titre distinct de son
    accroche, contrairement à une variante générée) et du texte brut complet
    pour la détection de motifs (preuve, urgence, lisibilité)."""
    return ScorableCopy(promise_text=analysis.hook, body_text=raw_text, cta_text=analysis.cta)


# ── Détection de motifs (FR) ────────────────────────────────────────────

_TRANSFORMATION_PATTERNS = [
    r"\benfin\b", r"\bsans\b", r"\bplus jamais\b", r"\bde\s+\S+\s+à\s+\S+\b",
    r"\ben\s+\d+\s*(jours?|semaines?|mois|ans?|heures?)\b", r"\bpassez de\b",
    r"\btransformez\b", r"\bdoublez\b", r"\btriplez\b", r"\bmultipliez\b",
]
_PROOF_PATTERNS = [
    r"\d+\s*%", r"\d+[\s+]*(clients?|utilisateurs?|membres?|entreprises?|témoignages?)",
    r"\btémoignage", r"\bavis\b", r"\bétude", r"\brecherche", r"\bgaranti", r"\bcertifié",
    r"\bprouvé", r"«[^»]{5,}»", r"\"[^\"]{5,}\"",
]
_AUDIENCE_PATTERNS = [
    r"\bpour les\b", r"\bpour des\b", r"\bpour tout\b", r"\bsi vous êtes\b", r"\bsi tu es\b",
    r"\bconçu pour\b", r"\bdestiné aux?\b", r"\bidéal pour\b", r"\bspécialement pour\b",
]
_BULLET_LINE = re.compile(r"^\s*([-•✓✔*]|\d+[.)])\s+", re.MULTILINE)
_VALUE_STACKING_PATTERNS = [r"\binclus\b", r"\bbonus\b", r"\bgratuit", r"\boffert"]
_URGENCY_PATTERNS = [
    r"\baujourd'hui\b", r"\bmaintenant\b", r"\bdernière chance\b", r"\bexpire", r"\blimité",
    r"\bplaces? restantes?\b", r"\boffre limitée\b", r"\bseulement\b", r"\bvite\b",
]
_CTA_VERBS = [
    "rejoignez", "réservez", "achetez", "commandez", "téléchargez", "inscrivez-vous",
    "profitez", "obtenez", "essayez", "démarrez", "commencez", "découvrez",
    "accédez", "je réserve", "je rejoins", "je commande", "je m'inscris", "j'en profite",
]
# CTA génériques bien identifiés comme faibles en copywriting direct-response
# (liste fermée et objective, pas un jugement au cas par cas) — plafonne le
# score même s'ils sont courts et commencent par un verbe.
_GENERIC_CTA_PHRASES = [
    "cliquez ici", "cliquer ici", "en savoir plus", "soumettre", "envoyer", "valider", "ici",
]


def _count_matches(patterns: list[str], text: str) -> int:
    text_lower = text.lower()
    return sum(1 for p in patterns if re.search(p, text_lower, re.IGNORECASE))


def _score_promise_clarity(promise_text: str) -> CriterionScore:
    max_points = _MAX_POINTS["promise_clarity"]
    if not promise_text.strip():
        return CriterionScore("promise_clarity", "Promesse / transformation dans le titre", 0, max_points, "Titre vide.")
    hits = _count_matches(_TRANSFORMATION_PATTERNS, promise_text)
    has_number = bool(re.search(r"\d", promise_text))
    score = min(max_points, hits * 7 + (4 if has_number else 0))
    detail = f"{hits} motif(s) de transformation détecté(s)" + (", chiffre présent" if has_number else "")
    return CriterionScore("promise_clarity", "Promesse / transformation dans le titre", score, max_points, detail)


def _score_proof(body_text: str) -> CriterionScore:
    max_points = _MAX_POINTS["proof"]
    hits = _count_matches(_PROOF_PATTERNS, body_text)
    score = min(max_points, hits * 5)
    detail = f"{hits} élément(s) de preuve/crédibilité détecté(s)" if hits else "Aucun élément de preuve détecté."
    return CriterionScore("proof", "Preuve / crédibilité", score, max_points, detail)


def _score_audience_clarity(body_text: str, promise_text: str) -> CriterionScore:
    max_points = _MAX_POINTS["audience_clarity"]
    combined = f"{promise_text} {body_text}"
    hits = _count_matches(_AUDIENCE_PATTERNS, combined)
    score = min(max_points, hits * 8)
    detail = f"{hits} formulation(s) d'adressage direct à l'audience" if hits else "Audience non explicitement nommée."
    return CriterionScore("audience_clarity", "Clarté de l'audience", score, max_points, detail)


def _score_conversion_elements(
    body_text: str, elements: list[FunnelStepElement] | None,
) -> CriterionScore:
    max_points = _MAX_POINTS["conversion_elements"]
    bullets = len(_BULLET_LINE.findall(body_text))
    value_hits = _count_matches(_VALUE_STACKING_PATTERNS, body_text)
    urgency_hits = _count_matches(_URGENCY_PATTERNS, body_text)
    active_elements = [e for e in (elements or []) if e.enabled]

    score = min(6, bullets * 2) + min(6, value_hits * 3) + min(4, urgency_hits * 2)
    score += min(4, len(active_elements) * 2)  # signal factuel, pas un motif de texte
    score = min(max_points, score)

    detail_parts = [f"{bullets} puce(s)/énumération(s)", f"{value_hits} motif(s) value stacking", f"{urgency_hits} motif(s) d'urgence texte"]
    if active_elements:
        detail_parts.append(f"{len(active_elements)} élément(s) de conversion actif(s) réellement attaché(s)")
    return CriterionScore("conversion_elements", "Éléments de conversion actifs", score, max_points, ", ".join(detail_parts))


def _count_syllables_fr(word: str) -> int:
    """Compte les syllabes par groupes de voyelles consécutives —
    approximation grossière (ne gère pas les diphtongues/e muets), suffisante
    pour une estimation relative entre deux textes, pas une mesure absolue."""
    groups = re.findall(r"[aeiouyàâäéèêëîïôöùûü]+", word.lower())
    return max(1, len(groups))


def _score_readability(body_text: str) -> CriterionScore:
    """Formule de Flesch adaptée au français (Kandel & Moles) :
    score = 207 - 1.015*(mots/phrases) - 73.6*(syllabes/mots).
    Résultat brut ~0-100+ remappé sur les points du critère."""
    max_points = _MAX_POINTS["readability"]
    words = re.findall(r"[a-zàâäéèêëîïôöùûüçA-ZÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ]+", body_text)
    # Le corps d'une pub est souvent structuré en puces/lignes sans
    # ponctuation finale plutôt qu'en phrases classiques — un saut de ligne
    # compte donc comme une frontière de phrase, sans quoi plusieurs puces
    # seraient comptées comme une seule phrase géante et fausseraient
    # complètement le ratio mots/phrase.
    sentences = [s for s in re.split(r"[.!?\n]+", body_text) if s.strip()]
    if not words or not sentences:
        return CriterionScore("readability", "Lisibilité", 0, max_points, "Texte insuffisant pour être évalué.")

    syllables = sum(_count_syllables_fr(w) for w in words)
    flesch_fr = 207 - 1.015 * (len(words) / len(sentences)) - 73.6 * (syllables / len(words))
    # Remap ~[30, 100] (difficile -> très facile) sur [0, max_points]
    normalized = max(0.0, min(1.0, (flesch_fr - 30) / 70))
    score = round(normalized * max_points)
    return CriterionScore("readability", "Lisibilité", score, max_points, f"Score de Flesch (FR) ≈ {flesch_fr:.0f}")


def _score_cta_clarity(cta_text: str) -> CriterionScore:
    max_points = _MAX_POINTS["cta_clarity"]
    if not cta_text.strip():
        return CriterionScore("cta_clarity", "CTA clair et unique", 0, max_points, "Aucun CTA détecté.")
    cta_clean = cta_text.strip().lower()
    is_generic = cta_clean in _GENERIC_CTA_PHRASES
    if is_generic:
        return CriterionScore(
            "cta_clarity", "CTA clair et unique", 2, max_points,
            f'"{cta_text.strip()}" est un CTA générique connu pour sous-performer.',
        )

    word_count = len(cta_text.split())
    starts_with_verb = any(cta_clean.startswith(v) for v in _CTA_VERBS)
    is_concise = word_count <= 8

    score = 0
    detail_parts = []
    if starts_with_verb:
        score += 8
        detail_parts.append("verbe d'action en tête")
    else:
        detail_parts.append("pas de verbe d'action reconnu en tête")
    if is_concise:
        score += 7
        detail_parts.append(f"{word_count} mot(s), concis")
    else:
        detail_parts.append(f"{word_count} mots, potentiellement dilué")
    score = min(max_points, score)
    return CriterionScore("cta_clarity", "CTA clair et unique", score, max_points, ", ".join(detail_parts))


def compute_copy_score(scorable: ScorableCopy, elements: list[FunnelStepElement] | None = None) -> CopyScore:
    """Calcule le score de structure copywriting sur 100 — voir le
    docstring du module pour ce que ce chiffre représente (et ne représente
    PAS)."""
    criteria = [
        _score_promise_clarity(scorable.promise_text),
        _score_proof(scorable.body_text),
        _score_audience_clarity(scorable.body_text, scorable.promise_text),
        _score_conversion_elements(scorable.body_text, elements),
        _score_readability(scorable.body_text),
        _score_cta_clarity(scorable.cta_text),
    ]
    return CopyScore(total=sum(c.score for c in criteria), criteria=criteria)


def compare_scores(before: CopyScore, after: CopyScore) -> CopyScoreComparison:
    before_by_slug = {c.slug: c.score for c in before.criteria}
    after_by_slug = {c.slug: c.score for c in after.criteria}
    delta_by_criterion = {slug: after_by_slug[slug] - before_by_slug[slug] for slug in after_by_slug}
    return CopyScoreComparison(
        before=before, after=after, delta_total=after.total - before.total,
        delta_by_criterion=delta_by_criterion,
    )

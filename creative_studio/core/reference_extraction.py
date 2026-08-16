"""Analyse d'un advertorial ou d'une page de vente déjà existante — c'est la
brique d'entrée du mode "Optimiser un existant" du Creative Studio.

Étape 1 du mode optimisation : extraire l'angle, le framework de copy déjà
utilisé (AIDA/PAS/Hormozi, ou hybride) et la structure (hook, preuve
sociale, urgence, CTA) d'un texte ou d'une URL fournis par l'utilisateur.
Le résultat (ExistingCopyAnalysis) sert ensuite d'ancrage à
core.copy_generation.generate_variant_from_reference pour générer des
variantes qui ne font varier qu'UN seul paramètre à la fois.

Ce module ne dépend pas de copy_generation.py — c'est copy_generation.py
qui l'importe, pas l'inverse, pour éviter tout cycle d'import.
"""

from __future__ import annotations

import io
from dataclasses import dataclass

import requests

try:
    import trafilatura
except ImportError:  # dépendance optionnelle tant que l'extraction d'URL n'est pas utilisée
    trafilatura = None

try:
    import pypdf
except ImportError:  # dépendance optionnelle tant que l'extraction PDF n'est pas utilisée
    pypdf = None

from creative_studio.core.llm_client import DEFAULT_MODEL, build_client, parse_structured_json_response
from creative_studio.core.variants import Framework

# Au-delà de cette taille, le texte de référence est tronqué avant d'être
# envoyé à Claude — même limite que MAX_PAGE_CHARS dans app.py pour rester
# cohérent avec l'existant.
MAX_REFERENCE_CHARS = 8000

VARY_DIMENSION_LABELS = {
    "hook": "l'accroche (hook)",
    "social_proof": "la preuve sociale",
    "urgency": "la structure d'urgence",
    "cta": "le CTA",
}

_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "detected_framework": {
            "type": "string",
            "enum": ["AIDA", "PAS", "hormozi"],
            "description": "Le framework de copywriting le plus proche de la structure observée, même si le texte est hybride",
        },
        "is_hybrid": {
            "type": "boolean",
            "description": "true si le texte mélange visiblement plusieurs frameworks plutôt que d'en suivre un seul strictement",
        },
        "hybrid_notes": {
            "type": "string",
            "description": "Si hybride : quels frameworks se mélangent et comment. Chaîne vide sinon.",
        },
        "angle": {
            "type": "string",
            "description": "L'angle marketing / la promesse centrale du texte, reformulée en une phrase",
        },
        "hook": {
            "type": "string",
            "description": "L'accroche d'origine (première phrase / idée qui capte l'attention)",
        },
        "body_summary": {
            "type": "string",
            "description": "Résumé de la structure du corps du texte (arguments, ordre, ton)",
        },
        "social_proof_notes": {
            "type": "string",
            "description": "Ce qui sert de preuve sociale dans le texte d'origine (témoignages, chiffres, autorité...), ou 'aucune' si absente",
        },
        "urgency_notes": {
            "type": "string",
            "description": "Ce qui crée l'urgence/la rareté dans le texte d'origine, ou 'aucune' si absente",
        },
        "cta": {
            "type": "string",
            "description": "L'appel à l'action d'origine",
        },
    },
    "required": [
        "detected_framework", "is_hybrid", "hybrid_notes", "angle", "hook",
        "body_summary", "social_proof_notes", "urgency_notes", "cta",
    ],
    "additionalProperties": False,
}

_ANALYSIS_SYSTEM_PROMPT = [
    {
        "type": "text",
        "text": (
            "Tu es un analyste en copywriting direct-response. On te donne le texte d'un "
            "advertorial ou d'une page de vente déjà publiée. Ta seule tâche est de "
            "diagnostiquer objectivement sa structure — angle, framework (AIDA / PAS / "
            "value stacking façon Hormozi, ou un mélange des deux), hook, preuve sociale, "
            "urgence et CTA — sans réécrire ni juger la qualité du texte. "
            "Réponds uniquement avec l'analyse structurée demandée."
        ),
    }
]


@dataclass
class ExistingCopyAnalysis:
    detected_framework: Framework
    is_hybrid: bool
    hybrid_notes: str
    angle: str
    hook: str
    body_summary: str
    social_proof_notes: str
    urgency_notes: str
    cta: str


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extrait le texte brut d'un PDF (ex : l'export "variante gagnante" du
    point 1) — chaque page est concaténée dans l'ordre. C'est la seule
    fonction du module qui parle à pypdf ; fetch_reference_text() et le mode
    upload du Funnel Builder passent tous les deux par elle.
    """
    if pypdf is None:
        raise RuntimeError("Le package 'pypdf' n'est pas installé (pip install pypdf).")
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    pages_text = [page.extract_text() or "" for page in reader.pages]
    text = "\n\n".join(p for p in pages_text if p.strip())
    if not text.strip():
        raise RuntimeError("Aucun texte exploitable extrait du PDF (PDF scanné/image sans texte ?).")
    return text


def _looks_like_pdf_url(url: str) -> bool:
    return url.lower().split("?")[0].endswith(".pdf")


def fetch_reference_text(raw_text_or_url: str) -> str:
    """Si l'entrée ressemble à une URL, en extrait le contenu texte — via
    pypdf si le lien pointe vers un PDF (ex : export "variante gagnante" du
    point 1), via trafilatura sinon (page web classique) ; si ce n'est pas
    une URL, la retourne telle quelle, comme texte brut déjà collé par
    l'utilisateur.
    """
    candidate = raw_text_or_url.strip()
    if candidate.startswith("http://") or candidate.startswith("https://"):
        if _looks_like_pdf_url(candidate):
            response = requests.get(candidate, timeout=20)
            response.raise_for_status()
            return extract_pdf_text(response.content)
        if trafilatura is None:
            raise RuntimeError("Le package 'trafilatura' n'est pas installé (pip install trafilatura).")
        downloaded = trafilatura.fetch_url(candidate)
        if not downloaded:
            raise RuntimeError(f"Impossible de récupérer le contenu de {candidate}.")
        extracted = trafilatura.extract(downloaded)
        if not extracted:
            raise RuntimeError(f"Aucun contenu exploitable extrait de {candidate}.")
        return extracted
    if not candidate:
        raise ValueError("Le texte ou l'URL de référence ne peut pas être vide.")
    return candidate


def analyze_existing_copy(raw_text_or_url: str, model: str = DEFAULT_MODEL) -> ExistingCopyAnalysis:
    """Analyse un advertorial/page de vente existant (texte brut, URL web ou
    lien PDF) et en extrait l'angle, le framework et la structure — étape 1
    du mode "Optimiser un existant", et étape optionnelle du Funnel Builder
    quand un lien de référence est fourni.
    """
    text = fetch_reference_text(raw_text_or_url)
    return _analyze_text(text, model)


def analyze_existing_copy_pdf_bytes(pdf_bytes: bytes, model: str = DEFAULT_MODEL) -> ExistingCopyAnalysis:
    """Même analyse que analyze_existing_copy(), pour un PDF déjà en mémoire
    (upload direct depuis le Funnel Builder) plutôt qu'un lien à télécharger.
    """
    text = extract_pdf_text(pdf_bytes)
    return _analyze_text(text, model)


def _analyze_text(text: str, model: str) -> ExistingCopyAnalysis:
    text = text[:MAX_REFERENCE_CHARS]

    client = build_client()
    response = client.messages.create(
        model=model,
        max_tokens=2048,
        system=_ANALYSIS_SYSTEM_PROMPT,
        thinking={"type": "adaptive"},
        output_config={
            "effort": "high",
            "format": {"type": "json_schema", "schema": _ANALYSIS_SCHEMA},
        },
        messages=[{"role": "user", "content": f"Analyse ce texte publicitaire :\n\n{text}"}],
    )

    data = parse_structured_json_response(response)
    return ExistingCopyAnalysis(
        detected_framework=Framework(data["detected_framework"]),
        is_hybrid=data["is_hybrid"],
        hybrid_notes=data.get("hybrid_notes", ""),
        angle=data["angle"],
        hook=data["hook"],
        body_summary=data["body_summary"],
        social_proof_notes=data["social_proof_notes"],
        urgency_notes=data["urgency_notes"],
        cta=data["cta"],
    )

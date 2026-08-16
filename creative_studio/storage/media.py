"""Stockage disque des médias (photos/vidéos) uploadés et attachés aux
étapes d'un funnel — même pattern que storage/db.py::DB_PATH (chemin
configurable via variable d'env, défaut à la racine du dépôt).

Seul le nom de fichier généré est stocké en base (FunnelStepMedia.location
pour source_type='upload') — jamais le binaire en base, comme demandé.
"""

from __future__ import annotations

import os
import uuid

MEDIA_DIR = os.environ.get(
    "LRS_CS_MEDIA_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".lrs_creative_studio_media"),
)

# Extensions acceptées à l'upload — whitelist volontairement stricte : le nom
# de fichier fourni par l'utilisateur n'est jamais réutilisé tel quel dans un
# chemin (voir save_uploaded_media), seule son extension est retenue après
# validation ici.
_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4", ".webm", ".mov"}


def ensure_media_dir() -> None:
    os.makedirs(MEDIA_DIR, exist_ok=True)


def save_uploaded_media(original_filename: str, data: bytes) -> str:
    """Sauvegarde les bytes uploadés sous un nom généré (évite collisions et
    tout risque de path traversal via un nom fourni par l'utilisateur) et
    retourne ce nom généré — c'est cette valeur qui va dans
    FunnelStepMedia.location, jamais le nom original.
    """
    ext = os.path.splitext(original_filename)[1].lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Extension de fichier non supportée : {ext or '(aucune)'} "
            f"(acceptées : {', '.join(sorted(_ALLOWED_EXTENSIONS))})"
        )
    ensure_media_dir()
    generated_name = f"{uuid.uuid4().hex}{ext}"
    with open(os.path.join(MEDIA_DIR, generated_name), "wb") as f:
        f.write(data)
    return generated_name


def media_path(filename: str) -> str:
    return os.path.join(MEDIA_DIR, filename)

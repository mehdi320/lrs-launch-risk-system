"""Configuration du serveur MCP — transport stdio par défaut, HTTP en option.

Rien ici ne s'active tout seul : c'est la commande de lancement (voir
README.md) qui décide, via ces variables d'environnement, si le serveur
tourne en stdio (Claude Desktop / Claude Code en local) ou en HTTP
(accès distant, à activer plus tard si besoin).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

Transport = Literal["stdio", "sse", "streamable-http"]


@dataclass(frozen=True)
class MCPConfig:
    transport: Transport
    host: str
    port: int


def load_config() -> MCPConfig:
    transport = os.environ.get("LRS_MCP_TRANSPORT", "stdio").strip().lower()
    if transport not in ("stdio", "sse", "streamable-http"):
        raise ValueError(
            f"LRS_MCP_TRANSPORT invalide : {transport!r} "
            "(attendu : 'stdio', 'sse' ou 'streamable-http')"
        )
    host = os.environ.get("LRS_MCP_HOST", "127.0.0.1")
    port = int(os.environ.get("LRS_MCP_PORT", "8765"))
    return MCPConfig(transport=transport, host=host, port=port)  # type: ignore[arg-type]

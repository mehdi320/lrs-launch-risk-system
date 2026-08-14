# Serveur MCP — LRS Creative Studio

Expose 4 outils du module Creative Studio via le [Model Context Protocol](https://modelcontextprotocol.io) :

| Outil | Rôle |
|---|---|
| `get_test_status(test_id)` | Statut d'un test A/B (lecture seule, ne consomme pas de "look" statistique) |
| `list_variants(test_id)` | Variantes d'un test + métriques live (expositions, conversions) |
| `trigger_generation(mode, input_data)` | Lance une génération — `mode` = `"from_scratch"` ou `"optimize_existing"` |
| `get_budget_priority(test_id=None)` | Priorisation budget (`core/prioritization.py`) — tous les tests actifs si `test_id` omis |

Il n'appelle que du code déjà existant dans `creative_studio/core` et `creative_studio/storage` — aucune logique métier dupliquée. Transport **stdio** par défaut (pour Claude Desktop / Claude Code en local) ; HTTP disponible en option pour un accès distant plus tard (voir plus bas), désactivé par défaut.

Ce serveur n'est **pas** démarré automatiquement par le dépôt, et n'est **pas** enregistré dans une configuration Claude Desktop existante — c'est à toi de le connecter quand tu es prêt (voir §Connexion à Claude Desktop).

## Installation

Dépendances séparées de `requirements.txt` à la racine (l'app Streamlit n'a pas besoin du SDK MCP). Recommandé : un venv dédié, ou au minimum le même environnement que `creative_studio/` puisque ce serveur l'importe directement.

```bash
cd /chemin/vers/lrs-launch-risk-system
pip install -r mcp_server/requirements.txt
pip install -r requirements.txt   # si pas déjà fait : anthropic, trafilatura, etc.
```

## Variables d'environnement

| Variable | Défaut | Rôle |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Requis pour `trigger_generation` (appelle Claude) |
| `LRS_CS_DB_PATH` | `.lrs_creative_studio.db` à la racine du dépôt | Base SQLite du module Creative Studio — **doit pointer vers le même fichier que l'app Streamlit** pour voir les mêmes produits/tests |
| `LRS_MCP_TRANSPORT` | `stdio` | `stdio`, `sse` ou `streamable-http` |
| `LRS_MCP_HOST` | `127.0.0.1` | Utilisé seulement si `LRS_MCP_TRANSPORT != stdio` |
| `LRS_MCP_PORT` | `8765` | Utilisé seulement si `LRS_MCP_TRANSPORT != stdio` |

## Lancer en local (test manuel)

```bash
cd /chemin/vers/lrs-launch-risk-system
python -m mcp_server
```

Tourne en stdio et attend une connexion MCP sur stdin/stdout (normal que ça n'affiche rien tant qu'aucun client ne s'y connecte — `Ctrl+C` pour arrêter).

## Connexion à Claude Desktop (à faire manuellement, quand prêt)

Éditer le fichier de config Claude Desktop :

- macOS : `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows : `%APPDATA%\Claude\claude_desktop_config.json`
- Linux : `~/.config/Claude/claude_desktop_config.json`

Ajouter une entrée dans `mcpServers` (remplacer le chemin et la clé API) :

```json
{
  "mcpServers": {
    "lrs-creative-studio": {
      "command": "python",
      "args": ["-m", "mcp_server"],
      "cwd": "/chemin/absolu/vers/lrs-launch-risk-system",
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-...",
        "LRS_CS_DB_PATH": "/chemin/absolu/vers/lrs-launch-risk-system/.lrs_creative_studio.db"
      }
    }
  }
}
```

Si ta version de Claude Desktop ignore `cwd` pour les serveurs stdio, ajoute plutôt `PYTHONPATH` dans `env` pointant vers le chemin absolu du dépôt — `python -m mcp_server` fonctionnera tant que la racine du dépôt est sur le path Python, peu importe le répertoire de travail effectif.

Redémarrer Claude Desktop après modification du fichier. Les 4 outils apparaissent alors sous le nom `lrs-creative-studio`.

## Connexion à Claude Code (local)

Même principe, via `claude mcp add` (voir `claude mcp add --help`) ou en éditant la config MCP du projet — pointer `command`/`args`/`cwd` comme ci-dessus.

## Passer en HTTP (accès distant — plus tard)

```bash
LRS_MCP_TRANSPORT=streamable-http LRS_MCP_HOST=0.0.0.0 LRS_MCP_PORT=8765 python -m mcp_server
```

Aucune authentification n'est ajoutée par ce code — à ne pas exposer sur un réseau non fiable sans mettre un reverse proxy authentifié devant, ou sans configurer l'auth du SDK MCP (`auth=...` dans `mcp_server/server.py`, non fait ici).

## Notes

- `get_test_status` et `list_variants` sont en lecture seule : ils ne recalculent jamais la significativité statistique (ce qui compterait comme une consultation supplémentaire au sens de la correction de peeking dans `core/stats.py`) — ils renvoient le dernier verdict déjà calculé, avec sa date, plus les compteurs bruts à jour.
- `trigger_generation` crée un produit à la volée si `input_data` ne contient pas de `product_id` valide (voir docstring de l'outil pour les champs requis selon le mode).
- Toutes les écritures passent par les mêmes repositories que l'UI Streamlit (`creative_studio/storage/repository.py`) — un test créé via ce serveur MCP est immédiatement visible dans l'onglet Creative Studio, et inversement.

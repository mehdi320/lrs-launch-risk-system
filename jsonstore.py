# LRS — Petit utilitaire de persistance JSON partagé entre app.py et pilot_server.py.

import json
import os


def load_json_file(path, default):
    """Charge un fichier JSON. `default` est une valeur ou une factory
    (list, dict, callable) utilisée si le fichier est absent ou invalide."""
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default() if callable(default) else default


def save_json_file(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass  # Silencieux si pas de droits d'écriture (Streamlit Cloud)

"""
webhook_server.py — Serveur Flask qui reçoit les ventes Systeme.io via webhook.

Configure côté Systeme.io :
    URL : http://localhost:5000/webhook/systemeio
    Événement : order.completed (ou sale)

Variables d'environnement optionnelles :
    WEBHOOK_SECRET   : clé secrète pour valider la signature (recommandé)
    PORT             : port d'écoute (défaut : 5000)

Usage :
    python webhook_server.py
"""

import hashlib
import hmac
import json
import logging
import os
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request

import db

load_dotenv()

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("tracker.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")


# ── Validation de signature ───────────────────────────────────────────────────

def _verify_signature(payload_bytes: bytes, signature_header: str) -> bool:
    """
    Vérifie la signature HMAC-SHA256 envoyée par Systeme.io.
    Si WEBHOOK_SECRET n'est pas configuré, la vérification est ignorée.
    """
    if not WEBHOOK_SECRET:
        logger.warning("WEBHOOK_SECRET non configuré — vérification de signature désactivée")
        return True

    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()

    # Systeme.io envoie parfois le préfixe "sha256="
    received = signature_header.replace("sha256=", "")
    return hmac.compare_digest(expected, received)


# ── Extraction des UTM ────────────────────────────────────────────────────────

def _extract_utms(payload: dict) -> dict:
    """
    Tente d'extraire les UTM depuis plusieurs emplacements possibles du payload.
    Systeme.io peut les placer dans :
      - payload["utm_parameters"]
      - payload["order"]["utm_parameters"]
      - payload["contact"]["utm_parameters"]
    """
    candidates = [
        payload,
        payload.get("order", {}),
        payload.get("contact", {}),
        payload.get("data", {}),
    ]

    for source in candidates:
        if not isinstance(source, dict):
            continue
        utm = source.get("utm_parameters") or source.get("utm") or {}
        if utm:
            return {
                "utm_source":   utm.get("utm_source") or utm.get("source", ""),
                "utm_campaign": utm.get("utm_campaign") or utm.get("campaign", ""),
                "utm_medium":   utm.get("utm_medium") or utm.get("medium", ""),
                "utm_content":  utm.get("utm_content") or utm.get("content", ""),
                "utm_term":     utm.get("utm_term") or utm.get("term", ""),
            }

    # Fallback : chercher directement à la racine
    return {
        "utm_source":   payload.get("utm_source", ""),
        "utm_campaign": payload.get("utm_campaign", ""),
        "utm_medium":   payload.get("utm_medium", ""),
        "utm_content":  payload.get("utm_content", ""),
        "utm_term":     payload.get("utm_term", ""),
    }


def _extract_sale_data(payload: dict) -> dict:
    """
    Normalise les champs de vente depuis le payload Systeme.io.
    Adapte selon la structure réelle de ton compte.
    """
    # Identifiant de la vente
    sale_id = (
        payload.get("id")
        or payload.get("order_id")
        or payload.get("order", {}).get("id")
        or str(uuid.uuid4())  # fallback UUID si absent
    )

    # Montant
    order = payload.get("order", payload)
    amount = float(
        order.get("amount")
        or order.get("total")
        or order.get("price")
        or 0
    )

    # Email
    email = (
        payload.get("email")
        or payload.get("contact", {}).get("email")
        or order.get("email")
        or ""
    )

    # Devise
    currency = (
        order.get("currency")
        or payload.get("currency")
        or "EUR"
    ).upper()

    # Date de création
    created_at = (
        payload.get("created_at")
        or payload.get("order", {}).get("created_at")
        or datetime.now(timezone.utc).isoformat()
    )

    utms = _extract_utms(payload)

    return {
        "sale_id":      str(sale_id),
        "email":        email,
        "amount":       amount,
        "currency":     currency,
        "created_at":   created_at,
        **utms,
    }


# ── Route principale ──────────────────────────────────────────────────────────

@app.route("/webhook/systemeio", methods=["POST"])
def receive_sale() -> Response:
    """Endpoint de réception des ventes Systeme.io."""
    payload_bytes = request.get_data()

    # Log tous les headers pour identifier celui de Systeme.io
    logger.info("Headers recus : %s", dict(request.headers))

    # Vérification de signature — désactivée temporairement pour debug
    # sig = request.headers.get("X-Systemeio-Signature", "")
    # if not _verify_signature(payload_bytes, sig):
    #     logger.warning("Signature webhook invalide — requête rejetée")
    #     return jsonify({"error": "signature invalide"}), 401

    # Log le payload brut pour debug
    logger.info("Content-Type : %s", request.content_type)
    logger.info("Payload brut : %s", payload_bytes[:500])

    # Parsing : JSON ou form-encodé
    content_type = request.content_type or ""
    if "application/json" in content_type:
        try:
            payload = json.loads(payload_bytes)
        except json.JSONDecodeError as e:
            logger.error("Payload JSON malformé : %s | brut : %s", e, payload_bytes[:200])
            return jsonify({"error": "JSON invalide"}), 400
    elif "application/x-www-form-urlencoded" in content_type or "multipart" in content_type:
        payload = request.form.to_dict()
    else:
        # Tentative JSON par défaut
        try:
            payload = json.loads(payload_bytes) if payload_bytes else {}
        except json.JSONDecodeError:
            payload = request.form.to_dict()

    logger.info("Webhook reçu : %s", json.dumps(payload, ensure_ascii=False, default=str)[:300])

    # Extraction et insertion
    try:
        sale = _extract_sale_data(payload)

        sql = """
            INSERT OR IGNORE INTO sales
                (sale_id, email, amount, currency,
                 utm_source, utm_campaign, utm_medium, utm_content, utm_term,
                 created_at, raw_payload)
            VALUES
                (:sale_id, :email, :amount, :currency,
                 :utm_source, :utm_campaign, :utm_medium, :utm_content, :utm_term,
                 :created_at, :raw_payload)
        """
        sale["raw_payload"] = json.dumps(payload, ensure_ascii=False)

        with db.get_connection() as conn:
            conn.execute(sql, sale)

        logger.info(
            "Vente enregistrée : id=%s email=%s amount=%.2f %s utm_content=%s",
            sale["sale_id"], sale["email"], sale["amount"],
            sale["currency"], sale["utm_content"],
        )
        return jsonify({"status": "ok", "sale_id": sale["sale_id"]}), 200

    except Exception as e:
        logger.exception("Erreur lors du traitement du webhook : %s", e)
        return jsonify({"error": "erreur interne"}), 500


@app.route("/health", methods=["GET"])
def health() -> Response:
    """Endpoint de santé pour vérifier que le serveur tourne."""
    return jsonify({"status": "ok", "db": str(db.DB_PATH)}), 200


# ── Démarrage ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    db.init_db()
    port = int(os.environ.get("PORT", 5000))
    logger.info("Serveur webhook démarré sur http://localhost:%d", port)
    print(f"Endpoint : http://localhost:{port}/webhook/systemeio")
    app.run(host="0.0.0.0", port=port, debug=False)

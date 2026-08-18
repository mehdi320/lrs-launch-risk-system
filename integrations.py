# LRS — Intégrations sortantes (Slack, Google Sheets, Notion)
#
# Extrait de app.py (send_slack_notification, export_to_sheets, export_to_notion)
# pour être réutilisé par pilot_server.py. Chaque fonction lit ses identifiants
# depuis les mêmes variables d'environnement que l'app Streamlit — configurez
# .env pour les activer, sinon elles échouent proprement avec un message clair.

import json
import os

import requests

APP_VERSION = "3.5"


def get_integration_config():
    return {
        "slack_webhook": os.getenv("SLACK_WEBHOOK_URL", ""),
        "sheets_creds": os.getenv("GOOGLE_SHEETS_CREDS", ""),
        "sheets_id": os.getenv("GOOGLE_SHEETS_ID", ""),
        "notion_token": os.getenv("NOTION_TOKEN", ""),
        "notion_db": os.getenv("NOTION_DATABASE_ID", ""),
    }


def send_slack_notification(result, meta):
    cfg = get_integration_config()
    webhook = cfg["slack_webhook"]
    if not webhook:
        raise ValueError("SLACK_WEBHOOK_URL non configuré.")

    c = result.get("_c", {})
    score = c.get("score", 0)
    decision = c.get("decision", "")
    url_or_offer = meta.get("url") or meta.get("offer_type", "")
    ts = meta.get("timestamp", "")
    mode = meta.get("mode", "")
    emoji = "🔴" if score <= 9 else "🟡" if score <= 14 else "🟢"

    fp = result.get("fix_plan", {})
    top = fp.get("top_priority_action", {})
    top_txt = top.get("what", "") if top else ""

    text = (
        f"{emoji} *LRS™ Audit — {score}/20 — {decision}*\n"
        f"*{url_or_offer}*  ·  {ts}  ·  {mode}\n"
    )
    if top_txt:
        text += f">🎯 {top_txt}\n"

    payload = {
        "text": text,
        "blocks": [
            {"type": "section", "text": {"type": "mrkdwn", "text": text}},
            {"type": "divider"},
            {"type": "context", "elements": [
                {"type": "mrkdwn", "text": f"Généré par *LRS™ V{APP_VERSION}* — Launch Risk System"}
            ]},
        ],
    }
    resp = requests.post(webhook, json=payload, timeout=10)
    if resp.status_code not in (200, 204):
        raise ValueError(f"Slack répondu {resp.status_code}: {resp.text[:200]}")


def export_to_sheets(result, meta):
    cfg = get_integration_config()
    creds_s = cfg["sheets_creds"]
    sheet_id = cfg["sheets_id"]
    if not creds_s or not sheet_id:
        raise ValueError("GOOGLE_SHEETS_CREDS ou GOOGLE_SHEETS_ID non configurés.")

    try:
        creds_dict = json.loads(creds_s)
    except Exception:
        raise ValueError("GOOGLE_SHEETS_CREDS : JSON invalide.")

    import base64
    import time as _time

    iat = int(_time.time())
    exp = iat + 3600
    scope = "https://www.googleapis.com/auth/spreadsheets"
    jwt_header = base64.urlsafe_b64encode(json.dumps({"alg": "RS256", "typ": "JWT"}).encode()).rstrip(b"=")
    jwt_claims = base64.urlsafe_b64encode(json.dumps({
        "iss": creds_dict["client_email"],
        "sub": creds_dict["client_email"],
        "aud": "https://oauth2.googleapis.com/token",
        "iat": iat, "exp": exp, "scope": scope,
    }).encode()).rstrip(b"=")
    signing_input = jwt_header + b"." + jwt_claims

    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
        private_key = serialization.load_pem_private_key(creds_dict["private_key"].encode(), password=None)
        signature = private_key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
        sig_b64 = base64.urlsafe_b64encode(signature).rstrip(b"=")
        jwt_token = (signing_input + b"." + sig_b64).decode()
    except ImportError:
        raise ValueError("Package 'cryptography' requis pour Google Sheets. Ajoutez `cryptography` à requirements.txt.")

    token_resp = requests.post("https://oauth2.googleapis.com/token", data={
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": jwt_token,
    }, timeout=15)
    if token_resp.status_code != 200:
        raise ValueError(f"Erreur token Google: {token_resp.text[:200]}")
    access_token = token_resp.json()["access_token"]

    c = result.get("_c", {})
    row = [
        meta.get("timestamp", ""), meta.get("url", meta.get("offer_type", "")),
        meta.get("mode", ""), meta.get("platform", ""),
        c.get("score", 0), c.get("decision", ""),
        c.get("hook", 0), c.get("offer", 0), c.get("trust", 0), c.get("friction", 0),
        (result.get("fix_plan", {}).get("top_priority_action", {}) or {}).get("what", ""),
    ]

    url_api = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}"
        f"/values/A1:append?valueInputOption=USER_ENTERED&insertDataOption=INSERT_ROWS"
    )
    resp = requests.post(
        url_api,
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
        json={"values": [row]},
        timeout=15,
    )
    if resp.status_code not in (200, 201):
        raise ValueError(f"Sheets API {resp.status_code}: {resp.text[:200]}")


def export_to_notion(result, meta):
    cfg = get_integration_config()
    token = cfg["notion_token"]
    db_id = cfg["notion_db"]
    if not token or not db_id:
        raise ValueError("NOTION_TOKEN ou NOTION_DATABASE_ID non configurés.")

    c = result.get("_c", {})
    score = c.get("score", 0)
    decision = c.get("decision", "")
    ts = meta.get("timestamp", "")
    url_val = meta.get("url", meta.get("offer_type", ""))
    mode = meta.get("mode", "")
    platform = meta.get("platform", "")
    hook = c.get("hook", 0)
    offer_sc = c.get("offer", 0)
    trust = c.get("trust", 0)
    friction = c.get("friction", 0)
    top_txt = (result.get("fix_plan", {}).get("top_priority_action", {}) or {}).get("what", "")

    page_title = f"LRS Audit — {score}/20 — {url_val[:60]}"

    notion_payload = {
        "parent": {"database_id": db_id},
        "properties": {
            "Name": {"title": [{"text": {"content": page_title}}]},
            "Date": {"rich_text": [{"text": {"content": ts}}]},
            "URL": {"url": url_val} if url_val.startswith("http") else {"rich_text": [{"text": {"content": url_val}}]},
            "Mode": {"select": {"name": mode}},
            "Platform": {"select": {"name": platform}},
            "Score": {"number": score},
            "Decision": {"rich_text": [{"text": {"content": decision}}]},
            "Hook": {"number": hook},
            "Offer": {"number": offer_sc},
            "Trust": {"number": trust},
            "Friction": {"number": friction},
            "Top Action": {"rich_text": [{"text": {"content": top_txt}}]},
        },
        "children": [
            {
                "object": "block", "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content":
                    f"Score: {score}/20 — {decision}\n"
                    f"Hook: {hook}/5 · Offer: {offer_sc}/5 · Trust: {trust}/5 · Friction: {friction}/5\n"
                    f"Top action: {top_txt}\n\nGénéré par LRS™ V{APP_VERSION}"
                }}]},
            }
        ],
    }

    resp = requests.post(
        "https://api.notion.com/v1/pages",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        },
        json=notion_payload,
        timeout=15,
    )
    if resp.status_code not in (200, 201):
        raise ValueError(f"Notion API {resp.status_code}: {resp.text[:200]}")

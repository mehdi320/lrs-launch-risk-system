"""
sync_meta.py — Synchronise les insights Meta Ads dans la base locale.

Variables d'environnement requises :
    META_ACCESS_TOKEN    : token d'accès longue durée
    META_AD_ACCOUNT_ID   : ex. act_123456789

Usage :
    python sync_meta.py              # 30 derniers jours (défaut)
    python sync_meta.py --days 7     # 7 derniers jours
"""

import argparse
import json
import logging
import os
import time
from datetime import date, timedelta

from dotenv import load_dotenv
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adsinsights import AdsInsights
from facebook_business.exceptions import FacebookRequestError

import db

load_dotenv()

# ── Configuration du logging ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("tracker.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# ── Constantes Meta API ───────────────────────────────────────────────────────
RATE_LIMIT_PAUSE = 60       # secondes d'attente si rate limit atteint
MAX_RETRIES = 3
PAGE_SIZE = 500             # insights par requête


def init_meta_api() -> None:
    """Initialise le SDK facebook-business avec les credentials .env."""
    token = os.environ.get("META_ACCESS_TOKEN")
    app_id = os.environ.get("META_APP_ID", "")
    app_secret = os.environ.get("META_APP_SECRET", "")

    if not token:
        raise EnvironmentError("META_ACCESS_TOKEN manquant dans .env")

    FacebookAdsApi.init(app_id, app_secret, token)
    logger.info("API Meta initialisée (account: %s)", os.environ.get("META_AD_ACCOUNT_ID"))


def fetch_insights(since: date, until: date) -> list[dict]:
    """
    Récupère les insights niveau 'ad' entre since et until (inclus).
    Gère la pagination et les rate limits automatiquement.
    """
    account_id = os.environ.get("META_AD_ACCOUNT_ID")
    if not account_id:
        raise EnvironmentError("META_AD_ACCOUNT_ID manquant dans .env")

    account = AdAccount(account_id)

    params = {
        "level": "ad",
        "time_increment": 1,           # granularité : 1 ligne par jour
        "time_range": {
            "since": since.isoformat(),
            "until": until.isoformat(),
        },
        "limit": PAGE_SIZE,
    }

    fields = [
        AdsInsights.Field.date_start,
        AdsInsights.Field.campaign_id,
        AdsInsights.Field.campaign_name,
        AdsInsights.Field.adset_id,
        AdsInsights.Field.adset_name,
        AdsInsights.Field.ad_id,
        AdsInsights.Field.ad_name,
        AdsInsights.Field.spend,
        AdsInsights.Field.impressions,
        AdsInsights.Field.clicks,
        AdsInsights.Field.actions,
        AdsInsights.Field.action_values,
    ]

    rows = []
    attempt = 0

    while attempt < MAX_RETRIES:
        try:
            cursor = account.get_insights(fields=fields, params=params)
            # Parcourir toutes les pages
            for insight in cursor:
                rows.append(dict(insight))
            logger.info("Insights récupérés : %d lignes", len(rows))
            return rows
        except FacebookRequestError as e:
            if e.http_status() == 429 or "rate limit" in str(e).lower():
                logger.warning(
                    "Rate limit Meta atteint — pause %ds (tentative %d/%d)",
                    RATE_LIMIT_PAUSE, attempt + 1, MAX_RETRIES,
                )
                time.sleep(RATE_LIMIT_PAUSE)
                attempt += 1
            else:
                logger.error("Erreur API Meta : %s", e)
                raise

    raise RuntimeError(f"Échec après {MAX_RETRIES} tentatives (rate limit persistant)")


def _extract_action_value(data: dict, action_type: str, field: str = "actions") -> float:
    """Extrait la valeur d'une action spécifique dans le tableau actions/action_values."""
    for entry in data.get(field, []):
        if entry.get("action_type") == action_type:
            return float(entry.get("value", 0))
    return 0.0


def upsert_insights(rows: list[dict]) -> int:
    """
    Insère ou met à jour les lignes dans ad_spend.
    Clé de déduplication : (date, ad_id).
    Retourne le nombre de lignes traitées.
    """
    sql = """
        INSERT INTO ad_spend
            (date, campaign_id, campaign_name, adset_id, adset_name,
             ad_id, ad_name, spend, impressions, clicks,
             meta_purchases, meta_revenue, synced_at)
        VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT (date, ad_id) DO UPDATE SET
            campaign_name   = excluded.campaign_name,
            adset_name      = excluded.adset_name,
            ad_name         = excluded.ad_name,
            spend           = excluded.spend,
            impressions     = excluded.impressions,
            clicks          = excluded.clicks,
            meta_purchases  = excluded.meta_purchases,
            meta_revenue    = excluded.meta_revenue,
            synced_at       = excluded.synced_at
    """

    records = []
    for row in rows:
        records.append((
            row.get("date_start"),
            row.get("campaign_id"),
            row.get("campaign_name"),
            row.get("adset_id"),
            row.get("adset_name"),
            row.get("ad_id"),
            row.get("ad_name"),
            float(row.get("spend", 0)),
            int(row.get("impressions", 0)),
            int(row.get("clicks", 0)),
            _extract_action_value(row, "purchase", "actions"),
            _extract_action_value(row, "purchase", "action_values"),
        ))

    with db.get_connection() as conn:
        conn.executemany(sql, records)

    logger.info("Upsert terminé : %d enregistrements", len(records))
    return len(records)


def sync(days: int = 30) -> None:
    """Point d'entrée principal : sync des N derniers jours."""
    db.init_db()
    init_meta_api()

    until = date.today() - timedelta(days=1)   # hier (données stables)
    since = until - timedelta(days=days - 1)

    logger.info("Sync Meta Ads : %s → %s (%d jours)", since, until, days)

    rows = fetch_insights(since, until)
    count = upsert_insights(rows)

    logger.info("Sync terminée — %d lignes dans ad_spend", count)
    print(f"✓ Sync terminée : {count} lignes ({since} → {until})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync Meta Ads insights → SQLite")
    parser.add_argument("--days", type=int, default=30, help="Nombre de jours à récupérer")
    args = parser.parse_args()
    sync(days=args.days)

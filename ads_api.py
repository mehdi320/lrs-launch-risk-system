# LRS — Connecteurs API pub (Meta Ads, TikTok Ads)
#
# Extrait de app.py (fetch_meta_campaigns, fetch_tiktok_campaigns) pour être
# réutilisé par pilot_server.py. Nécessite un access token + account id
# fournis par l'utilisateur (voir onglet Suivi > Connexion API Pub) — ne
# fonctionne qu'une fois ces identifiants renseignés.

import datetime

import requests


def fetch_meta_campaigns(access_token, ad_account_id, date_preset="last_7d"):
    """
    Récupère les campagnes Meta Ads avec leurs métriques via Marketing API v19.
    Retourne une liste de dicts {name, campaign_id, spend, impressions, clicks, ctr, cpc, roas, cpa, purchases}.
    """
    acc_id = ad_account_id.strip().lstrip("act_")
    url = f"https://graph.facebook.com/v19.0/act_{acc_id}/campaigns"
    params = {
        "access_token": access_token,
        "fields": "id,name,status,objective",
        "limit": 20,
    }
    resp = requests.get(url, params=params, timeout=15)
    if resp.status_code != 200:
        raise ValueError(f"Meta API {resp.status_code}: {resp.json().get('error', {}).get('message', 'Erreur inconnue')}")

    campaigns_raw = resp.json().get("data", [])
    results = []

    for camp in campaigns_raw[:10]:
        cid = camp["id"]
        cname = camp["name"]
        cstat = camp.get("status", "")

        ins_url = f"https://graph.facebook.com/v19.0/{cid}/insights"
        ins_params = {
            "access_token": access_token,
            "date_preset": date_preset,
            "fields": "spend,impressions,clicks,ctr,cpc,actions,purchase_roas",
            "level": "campaign",
        }
        ins_resp = requests.get(ins_url, params=ins_params, timeout=15)
        if ins_resp.status_code != 200:
            continue
        ins_data = ins_resp.json().get("data", [])
        if not ins_data:
            continue
        ins = ins_data[0]

        spend = float(ins.get("spend", 0))
        impressions = int(ins.get("impressions", 0))
        clicks = int(ins.get("clicks", 0))
        ctr_v = float(ins.get("ctr", 0))
        cpc_v = float(ins.get("cpc", 0))

        roas_raw = ins.get("purchase_roas", [])
        roas_v = float(roas_raw[0]["value"]) if roas_raw else 0.0

        actions = ins.get("actions", [])
        purchases = next((int(a["value"]) for a in actions if a["action_type"] == "purchase"), 0)
        cpa_v = round(spend / purchases, 2) if purchases > 0 else 0.0

        results.append({
            "name": cname,
            "campaign_id": cid,
            "status": cstat,
            "spend": round(spend, 2),
            "impressions": impressions,
            "clicks": clicks,
            "ctr": round(ctr_v, 2),
            "cpc": round(cpc_v, 2),
            "roas": round(roas_v, 2),
            "cpa": cpa_v,
            "purchases": purchases,
        })

    return results


def fetch_tiktok_campaigns(access_token, advertiser_id, date_range_days=7):
    """
    Récupère les campagnes TikTok Ads via Marketing API v1.3.
    Retourne une liste de dicts similaires à Meta.
    """
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=date_range_days)

    headers = {"Access-Token": access_token, "Content-Type": "application/json"}

    camp_url = "https://business-api.tiktok.com/open_api/v1.3/campaign/get/"
    camp_resp = requests.get(camp_url, headers=headers, params={
        "advertiser_id": advertiser_id,
        "page_size": 10,
        "fields": '["campaign_id","campaign_name","status","objective_type"]',
    }, timeout=15)

    if camp_resp.status_code != 200:
        raise ValueError(f"TikTok API {camp_resp.status_code}: {camp_resp.text[:200]}")

    data_tt = camp_resp.json()
    if data_tt.get("code") != 0:
        raise ValueError(f"TikTok: {data_tt.get('message', 'Erreur inconnue')}")

    campaigns_tt = data_tt.get("data", {}).get("list", [])[:10]
    results = []

    for camp in campaigns_tt:
        cid = camp["campaign_id"]
        cname = camp["campaign_name"]

        ins_url = "https://business-api.tiktok.com/open_api/v1.3/report/integrated/get/"
        ins_resp = requests.get(ins_url, headers=headers, params={
            "advertiser_id": advertiser_id,
            "report_type": "BASIC",
            "dimensions": '["campaign_id"]',
            "metrics": '["spend","impressions","clicks","ctr","cpc","conversion","cost_per_conversion","real_time_conversion_rate"]',
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "filters": f'[{{"field_name":"campaign_id","filter_type":"IN","filter_value":"[\\"{cid}\\"]"}}]',
            "page_size": 1,
        }, timeout=15)

        if ins_resp.status_code != 200:
            continue
        ins_data_tt = ins_resp.json().get("data", {}).get("list", [])
        if not ins_data_tt:
            continue

        m = ins_data_tt[0].get("metrics", {})
        spend = float(m.get("spend", 0))
        clicks = int(m.get("clicks", 0))
        ctr_v = float(m.get("ctr", 0))
        cpc_v = float(m.get("cpc", 0))
        conv = int(m.get("conversion", 0))
        cpa_v = float(m.get("cost_per_conversion", 0))
        roas_v = round(spend / cpa_v, 2) if cpa_v > 0 and spend > 0 else 0.0

        results.append({
            "name": cname,
            "campaign_id": str(cid),
            "status": camp.get("status", ""),
            "spend": round(spend, 2),
            "impressions": int(m.get("impressions", 0)),
            "clicks": clicks,
            "ctr": round(ctr_v * 100, 2),
            "cpc": round(cpc_v, 2),
            "roas": roas_v,
            "cpa": round(cpa_v, 2),
            "purchases": conv,
        })

    return results


def correlate_stats(lrs_score, ctr, cpc, roas, cpa):
    """
    Croise les stats de campagne avec le score LRS pour générer des diagnostics.
    Retourne une liste de messages diagnostics priorisés.
    """
    diags = []

    if ctr is not None and ctr < 1.0:
        diags.append({
            "level": "danger", "crit": "Hook",
            "msg": f"CTR {ctr:.2f}% est très faible (< 1%). Ton hook pub ne capte pas l'attention. "
                   "Teste 3 nouvelles accroches et change le visuel.",
        })
    elif ctr is not None and ctr < 2.0:
        diags.append({
            "level": "warning", "crit": "Hook",
            "msg": f"CTR {ctr:.2f}% est perfectible. Un bon CTR Meta est > 2%. Revois ton angle créatif.",
        })

    if cpc is not None and cpc > 1.5:
        diags.append({
            "level": "warning", "crit": "Hook",
            "msg": f"CPC {cpc:.2f}€ est élevé. Soit ta niche est très compétitive, soit ton Quality Score pub souffre d'un CTR bas.",
        })

    if roas is not None and roas < 2.0:
        diags.append({
            "level": "danger", "crit": "Offer / Trust",
            "msg": f"ROAS {roas:.1f}x est sous le seuil de rentabilité. "
                   "Le trafic arrive mais ne convertit pas — ton Offer Stack ou tes preuves sociales sont insuffisants.",
        })
    elif roas is not None and roas < 3.0:
        diags.append({
            "level": "warning", "crit": "Offer",
            "msg": f"ROAS {roas:.1f}x est rentable mais optimisable. "
                   "Renforce ta garantie et ton offer stack pour augmenter la valeur perçue.",
        })

    if cpa is not None and lrs_score is not None:
        if cpa > 50 and lrs_score < 12:
            diags.append({
                "level": "danger", "crit": "Friction",
                "msg": f"CPA {cpa:.0f}€ avec un score LRS de {lrs_score}/20 — le problème est clairement sur ta page. "
                       "Améliore ton score d'au moins 3 pts pour réduire significativement ton CPA.",
            })

    if lrs_score is not None:
        if lrs_score >= 15:
            diags.append({
                "level": "ok", "crit": "Score LRS",
                "msg": f"Score LRS {lrs_score}/20 — page bien optimisée. Si le ROAS reste bas, le problème est dans la qualité du trafic (audience, créa pub), pas dans la page.",
            })
        elif lrs_score < 10:
            diags.append({
                "level": "danger", "crit": "Score LRS",
                "msg": f"Score LRS {lrs_score}/20 — ta page est le goulot d'étranglement principal. Corriger les quick wins LRS avant d'augmenter le budget.",
            })

    return diags

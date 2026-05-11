"""
pages/performance.py — Page "Performance & ROAS" intégrée à LRS.

Anti-churn loop : Audit LRS → Lancement → Suivi ROAS → Alerte si chute → Re-audit.
Lit tracker/tracker.db (local) et .lrs_history.json (audits LRS).
"""

import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

# ── Accès au module tracker ───────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "tracker"))
import db  # noqa: E402

# ── Fichiers LRS ──────────────────────────────────────────────────────────────
HISTORY_FILE = ROOT / ".lrs_history.json"
LINKS_FILE   = ROOT / ".lrs_campaign_links.json"  # liaison audit ↔ campagne

# ── Config page ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Performance — LRS",
    page_icon="📈",
    layout="wide",
)

st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background: #07071a; color: #e0e0e0; }
    [data-testid="stSidebar"]          { background: #0f0f1a; }
    .metric-card {
        background: #0f0f1a; border: 1px solid #1e1e3a;
        border-radius: 10px; padding: 16px; text-align: center;
    }
    .section-title { color: #a78bfa; font-size: 1.1rem; font-weight: 600; }
    .alert-box {
        background: #2d0f0f; border: 1px solid #7f1d1d;
        border-radius: 8px; padding: 12px; margin: 8px 0;
    }
    .ok-box {
        background: #0f2d1a; border: 1px solid #14532d;
        border-radius: 8px; padding: 12px; margin: 8px 0;
    }
</style>
""", unsafe_allow_html=True)

st.title("📈 Performance & ROAS Réel")
st.caption("Meta Ads × Systeme.io — boucle anti-churn : Audit → Lancement → Suivi → Re-audit")

# ── Vérification DB ───────────────────────────────────────────────────────────
if not db.DB_PATH.exists():
    st.error("Base tracker introuvable. Lance `python tracker/sync_meta.py` d'abord.")
    st.stop()

db.init_db()


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_lrs_history() -> list[dict]:
    try:
        if HISTORY_FILE.exists():
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return []


def load_links() -> dict:
    try:
        if LINKS_FILE.exists():
            return json.loads(LINKS_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def save_links(links: dict) -> None:
    LINKS_FILE.write_text(json.dumps(links, ensure_ascii=False, indent=2), encoding="utf-8")


@st.cache_data(ttl=300)
def load_roas_data(since: str, until: str) -> pd.DataFrame:
    sql = """
        SELECT
            s.date, s.campaign_id, s.campaign_name,
            s.adset_id, s.adset_name, s.ad_id, s.ad_name,
            s.spend, s.impressions, s.clicks,
            s.meta_purchases, s.meta_revenue,
            COALESCE(sys.real_purchases, 0) AS real_purchases,
            COALESCE(sys.real_revenue,   0) AS real_revenue
        FROM ad_spend s
        LEFT JOIN (
            SELECT utm_content AS ad_id,
                   COUNT(*)    AS real_purchases,
                   SUM(amount) AS real_revenue
            FROM sales
            WHERE date(created_at) BETWEEN ? AND ?
              AND utm_content != '' AND utm_content IS NOT NULL
            GROUP BY utm_content
        ) sys ON sys.ad_id = s.ad_id
        WHERE s.date BETWEEN ? AND ?
    """
    conn = db.get_connection()
    df = pd.read_sql_query(sql, conn, params=(since, until, since, until))
    conn.close()
    return df


@st.cache_data(ttl=300)
def load_campaigns_list() -> list[str]:
    """Retourne la liste des campaign_name distincts dans ad_spend."""
    conn = db.get_connection()
    rows = conn.execute(
        "SELECT DISTINCT campaign_id, campaign_name FROM ad_spend ORDER BY campaign_name"
    ).fetchall()
    conn.close()
    return [f"{r['campaign_name']} ({r['campaign_id']})" for r in rows]


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — SÉLECTEUR DE PÉRIODE
# ═══════════════════════════════════════════════════════════════════════════════

col_period, col_level, _ = st.columns([2, 2, 4])

with col_period:
    period = st.selectbox(
        "Période",
        ["7 derniers jours", "14 derniers jours", "30 derniers jours", "Personnalisée"],
        index=2,
    )

today = date.today()
if period == "7 derniers jours":
    date_since, date_until = today - timedelta(7), today - timedelta(1)
elif period == "14 derniers jours":
    date_since, date_until = today - timedelta(14), today - timedelta(1)
elif period == "30 derniers jours":
    date_since, date_until = today - timedelta(30), today - timedelta(1)
else:
    c1, c2 = st.columns(2)
    date_since = c1.date_input("Du", value=today - timedelta(30))
    date_until = c2.date_input("Au", value=today - timedelta(1))

with col_level:
    level = st.selectbox("Agrégation", ["Campagne", "Adset", "Publicité (ad)"])

since_str = date_since.isoformat()
until_str = date_until.isoformat()

df_raw = load_roas_data(since_str, until_str)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — KPIs GLOBAUX
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("---")

if df_raw.empty:
    st.warning("Aucune donnée Meta pour cette période. Lance `python tracker/sync_meta.py`.")
else:
    total_spend = df_raw["spend"].sum()
    total_real  = df_raw["real_revenue"].sum()
    total_meta  = df_raw["meta_revenue"].sum()
    roas_reel   = round(total_real / total_spend, 2) if total_spend else 0
    roas_meta   = round(total_meta / total_spend, 2) if total_spend else 0
    ecart       = round((roas_reel - roas_meta) / roas_meta * 100, 1) if roas_meta else 0

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("💸 Dépense", f"{total_spend:,.2f} €")
    k2.metric("💰 Revenu réel", f"{total_real:,.2f} €")
    k3.metric("📈 ROAS Réel", f"{roas_reel}x")
    k4.metric("🤖 ROAS Meta (pixel)", f"{roas_meta}x")
    k5.metric("⚖️ Écart attribution", f"{ecart:+.1f}%",
              delta=f"{ecart:+.1f}%", delta_color="normal")

    st.markdown("---")

    # ── Tableau détaillé ─────────────────────────────────────────────────────
    LEVEL_GROUPS = {
        "Campagne":       ["campaign_id", "campaign_name"],
        "Adset":          ["campaign_id", "campaign_name", "adset_id", "adset_name"],
        "Publicité (ad)": ["campaign_id", "campaign_name", "adset_id", "adset_name", "ad_id", "ad_name"],
    }
    name_col = {"Campagne": "campaign_name", "Adset": "adset_name", "Publicité (ad)": "ad_name"}[level]

    df = df_raw.groupby(LEVEL_GROUPS[level], as_index=False).agg(
        spend=("spend", "sum"), meta_revenue=("meta_revenue", "sum"),
        real_revenue=("real_revenue", "sum"),
        real_purchases=("real_purchases", "sum"),
        meta_purchases=("meta_purchases", "sum"),
        clicks=("clicks", "sum"),
    )
    df["ROAS Réel"]  = df.apply(lambda r: round(r.real_revenue / r.spend, 2) if r.spend else 0, axis=1)
    df["ROAS Meta"]  = df.apply(lambda r: round(r.meta_revenue / r.spend, 2) if r.spend else 0, axis=1)
    df["Écart (%)"]  = df.apply(
        lambda r: round((r["ROAS Réel"] - r["ROAS Meta"]) / r["ROAS Meta"] * 100, 1)
        if r["ROAS Meta"] else None, axis=1
    )

    display = df[[name_col, "spend", "meta_purchases", "meta_revenue",
                  "real_purchases", "real_revenue", "ROAS Meta", "ROAS Réel", "Écart (%)"]].copy()
    display.columns = ["Nom", "Dépense (€)", "Achats Meta", "Revenu Meta (€)",
                       "Achats réels", "Revenu réel (€)", "ROAS Meta", "ROAS Réel", "Écart (%)"]

    st.subheader(f"Détail par {level.lower()}")
    st.dataframe(
        display.style
        .format({"Dépense (€)": "{:,.2f}", "Revenu Meta (€)": "{:,.2f}",
                 "Revenu réel (€)": "{:,.2f}", "ROAS Meta": "{:.2f}x", "ROAS Réel": "{:.2f}x",
                 "Écart (%)": lambda v: f"{v:+.1f}%" if pd.notna(v) else "—"})
        .applymap(
            lambda v: "background-color:#0f2d1a" if isinstance(v, float) and v >= 0
            else ("background-color:#2d0f0f" if isinstance(v, float) and v < 0 else ""),
            subset=["Écart (%)"]
        ),
        use_container_width=True, height=360,
    )

    # ── Graphique ROAS temporel ───────────────────────────────────────────────
    st.subheader("ROAS Réel vs ROAS Meta — évolution")
    chart = df_raw.groupby("date", as_index=False).agg(
        spend=("spend", "sum"),
        meta_revenue=("meta_revenue", "sum"),
        real_revenue=("real_revenue", "sum"),
    )
    chart["ROAS Meta"]  = chart.apply(lambda r: r.meta_revenue / r.spend if r.spend else 0, axis=1)
    chart["ROAS Réel"]  = chart.apply(lambda r: r.real_revenue / r.spend if r.spend else 0, axis=1)
    st.line_chart(chart.set_index("date")[["ROAS Meta", "ROAS Réel"]])

st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — CORRÉLATION SCORE LRS ↔ ROAS RÉEL
# Pièce maîtresse anti-churn : l'utilisateur voit que ses pages
# avec score LRS élevé génèrent un meilleur ROAS → il re-audite avant chaque lancement.
# ═══════════════════════════════════════════════════════════════════════════════

st.subheader("🔗 Corrélation Score LRS ↔ ROAS Réel")
st.caption(
    "Lie chaque audit LRS à la campagne Meta correspondante. "
    "LRS calcule ensuite si un score élevé prédit un meilleur ROAS."
)

history = load_lrs_history()
links   = load_links()
campaigns = load_campaigns_list()

if not history:
    st.info("Aucun audit LRS trouvé. Lance un audit depuis l'onglet principal pour commencer.")
elif not campaigns:
    st.info("Aucune campagne Meta synchronisée. Lance `python tracker/sync_meta.py`.")
else:
    st.markdown("**Étape 1 — Associe chaque audit LRS à sa campagne Meta**")
    st.caption("Cette liaison est sauvegardée automatiquement.")

    campaign_options = ["— Non lié —"] + campaigns
    updated = False

    rows_to_show = history[:15]  # 15 audits max affichés
    for i, entry in enumerate(rows_to_show):
        url       = entry.get("url", "—")
        score     = entry.get("score", 0)
        ts        = entry.get("timestamp", "")
        link_key  = f"{url}|{ts}"
        current   = links.get(link_key, "— Non lié —")

        current_idx = campaign_options.index(current) if current in campaign_options else 0

        col_url, col_score, col_select = st.columns([4, 1, 4])
        col_url.markdown(f"**{url[:60]}{'…' if len(url)>60 else ''}**  \n`{ts[:16]}`")
        col_score.metric("Score", f"{score}/100")
        chosen = col_select.selectbox(
            "Campagne Meta", campaign_options,
            index=current_idx, key=f"link_{i}",
            label_visibility="collapsed",
        )

        if chosen != current:
            links[link_key] = chosen
            updated = True

    if updated:
        save_links(links)
        st.cache_data.clear()
        st.success("Liaisons sauvegardées.")

    # ── Calcul corrélation ────────────────────────────────────────────────────
    # Construire un df avec score LRS + ROAS réel pour les audits liés
    corr_rows = []
    for entry in history:
        url      = entry.get("url", "")
        score    = entry.get("score")
        ts       = entry.get("timestamp", "")
        link_key = f"{url}|{ts}"
        linked   = links.get(link_key, "— Non lié —")

        if linked == "— Non lié —" or score is None:
            continue

        # Extraire campaign_id depuis la valeur "(act_xxx)"
        campaign_id = linked.split("(")[-1].rstrip(")") if "(" in linked else None
        campaign_name = linked.split(" (")[0] if "(" in linked else linked

        if not campaign_id or df_raw.empty:
            continue

        camp_df = df_raw[df_raw["campaign_id"] == campaign_id]
        if camp_df.empty:
            continue

        spend       = camp_df["spend"].sum()
        real_rev    = camp_df["real_revenue"].sum()
        roas_r      = round(real_rev / spend, 2) if spend else 0
        meta_rev    = camp_df["meta_revenue"].sum()
        roas_m      = round(meta_rev / spend, 2) if spend else 0

        corr_rows.append({
            "URL auditée":    url[:50],
            "Score LRS":      score,
            "Campagne":       campaign_name[:35],
            "Dépense (€)":    round(spend, 2),
            "ROAS Réel":      roas_r,
            "ROAS Meta":      roas_m,
            "Décision LRS":   entry.get("decision", "—"),
        })

    if corr_rows:
        st.markdown("---")
        st.markdown("**Étape 2 — Corrélation Score LRS ↔ ROAS Réel**")

        df_corr = pd.DataFrame(corr_rows).sort_values("Score LRS", ascending=False)
        st.dataframe(
            df_corr.style.background_gradient(subset=["Score LRS"], cmap="RdYlGn")
                         .background_gradient(subset=["ROAS Réel"], cmap="RdYlGn")
                         .format({"Dépense (€)": "{:,.2f}", "ROAS Réel": "{:.2f}x", "ROAS Meta": "{:.2f}x"}),
            use_container_width=True,
        )

        # Insight automatique
        if len(df_corr) >= 2:
            top    = df_corr[df_corr["Score LRS"] >= df_corr["Score LRS"].median()]
            bottom = df_corr[df_corr["Score LRS"] <  df_corr["Score LRS"].median()]
            avg_top    = top["ROAS Réel"].mean()
            avg_bottom = bottom["ROAS Réel"].mean()

            if avg_top > avg_bottom:
                delta_pct = round((avg_top - avg_bottom) / avg_bottom * 100) if avg_bottom else 0
                st.success(
                    f"Pages avec score LRS élevé → ROAS réel moyen **{avg_top:.2f}x** "
                    f"vs **{avg_bottom:.2f}x** pour les scores faibles (+{delta_pct}%). "
                    f"Le score LRS prédit bien la performance publicitaire."
                )
            else:
                st.info("Pas encore assez de données pour valider la corrélation. Continue à auditer et lier tes campagnes.")
    else:
        st.info("Lie au moins un audit à une campagne ci-dessus pour voir la corrélation.")

st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — ALERTES ROAS
# Si ROAS chute → alerte rouge + lien direct vers re-audit LRS
# ═══════════════════════════════════════════════════════════════════════════════

st.subheader("🚨 Alertes ROAS")
st.caption("Surveille les chutes de performance et déclenche un re-audit LRS si nécessaire.")

col_seuil, col_delta, _ = st.columns([2, 2, 4])
seuil_roas  = col_seuil.number_input("Seuil ROAS minimum", min_value=0.0, value=2.0, step=0.1)
seuil_chute = col_delta.number_input("Alerte si chute > (%)", min_value=0, value=20, step=5)

if not df_raw.empty:
    # Comparer 7 derniers jours vs 7 jours précédents
    mid   = today - timedelta(7)
    prev_since = (mid - timedelta(7)).isoformat()
    prev_until = (mid - timedelta(1)).isoformat()

    df_curr = load_roas_data(since_str, until_str)
    df_prev = load_roas_data(prev_since, prev_until)

    campaigns_curr = df_curr.groupby(["campaign_id", "campaign_name"]).agg(
        spend=("spend", "sum"), real_revenue=("real_revenue", "sum")
    ).reset_index()
    campaigns_curr["roas"] = campaigns_curr.apply(
        lambda r: round(r.real_revenue / r.spend, 2) if r.spend else 0, axis=1
    )

    campaigns_prev = df_prev.groupby("campaign_id").agg(
        real_revenue_prev=("real_revenue", "sum"), spend_prev=("spend", "sum")
    ).reset_index()
    campaigns_prev["roas_prev"] = campaigns_prev.apply(
        lambda r: round(r.real_revenue_prev / r.spend_prev, 2) if r.spend_prev else 0, axis=1
    )

    merged = campaigns_curr.merge(campaigns_prev[["campaign_id", "roas_prev"]], on="campaign_id", how="left")
    merged["roas_prev"] = merged["roas_prev"].fillna(0)
    merged["chute_pct"] = merged.apply(
        lambda r: round((r.roas - r.roas_prev) / r.roas_prev * 100, 1) if r.roas_prev else 0, axis=1
    )

    alertes = merged[(merged["roas"] < seuil_roas) | (merged["chute_pct"] <= -seuil_chute)]

    if alertes.empty:
        st.markdown('<div class="ok-box">✅ Toutes les campagnes sont au-dessus du seuil ROAS.</div>', unsafe_allow_html=True)
    else:
        for _, row in alertes.iterrows():
            raison = []
            if row["roas"] < seuil_roas:
                raison.append(f"ROAS réel {row['roas']}x < seuil {seuil_roas}x")
            if row["chute_pct"] <= -seuil_chute:
                raison.append(f"chute de {row['chute_pct']:+.1f}% vs semaine précédente")

            st.markdown(
                f'<div class="alert-box">'
                f'⚠️ <b>{row["campaign_name"]}</b> — {" | ".join(raison)}<br>'
                f'<small>ROAS actuel : {row["roas"]}x | Semaine préc. : {row["roas_prev"]}x | Dépense : {row["spend"]:,.2f} €</small>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown("**Recommandation :** retourne sur l'onglet principal LRS et re-audite la page de destination de ces campagnes.")

st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — VENTES NON ATTRIBUÉES
# ═══════════════════════════════════════════════════════════════════════════════

with st.expander("🔍 Ventes Systeme.io non attribuées (utm_content vide)"):
    sql_unattr = """
        SELECT sale_id, email, amount, currency, created_at,
               utm_source, utm_campaign, utm_medium, utm_content
        FROM sales
        WHERE date(created_at) BETWEEN ? AND ?
          AND (utm_content IS NULL OR utm_content = '')
        ORDER BY created_at DESC LIMIT 100
    """
    conn = db.get_connection()
    df_unattr = pd.read_sql_query(sql_unattr, conn, params=(since_str, until_str))
    conn.close()

    if df_unattr.empty:
        st.success("Toutes les ventes de la période ont un utm_content. Attribution 100%.")
    else:
        total_unattr = df_unattr["amount"].sum()
        st.warning(
            f"**{len(df_unattr)} ventes non attribuées** ({total_unattr:,.2f} €) — "
            "utm_content manquant. Vérifier la convention UTM dans Ads Manager : "
            "`utm_content={{ad.id}}`"
        )
        st.dataframe(df_unattr, use_container_width=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    f"Données : Meta Ads API (pixel) × Systeme.io (webhook). "
    f"Jointure sur utm_content = ad_id. "
    f"Période : {since_str} → {until_str}. "
    f"DB : {db.DB_PATH}"
)

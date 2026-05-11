"""
app.py — Dashboard Streamlit : ROAS réel Meta Ads × Systeme.io.

Usage :
    streamlit run app.py
"""

import sqlite3
from datetime import date, timedelta

import pandas as pd
import streamlit as st

import db

# ── Configuration de la page ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Meta Ads ROAS Tracker",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Meta Ads × Systeme.io — ROAS Réel")
st.caption("Croise les dépenses Meta avec les ventes réellement encaissées.")


# ── Sélecteur de période ──────────────────────────────────────────────────────
col_period, col_level, _ = st.columns([2, 2, 4])

with col_period:
    period = st.selectbox(
        "Période",
        options=["7 derniers jours", "14 derniers jours", "30 derniers jours", "Personnalisée"],
        index=2,
    )

today = date.today()

if period == "7 derniers jours":
    date_since = today - timedelta(days=7)
    date_until = today - timedelta(days=1)
elif period == "14 derniers jours":
    date_since = today - timedelta(days=14)
    date_until = today - timedelta(days=1)
elif period == "30 derniers jours":
    date_since = today - timedelta(days=30)
    date_until = today - timedelta(days=1)
else:
    col_since, col_until = st.columns(2)
    with col_since:
        date_since = st.date_input("Du", value=today - timedelta(days=30))
    with col_until:
        date_until = st.date_input("Au", value=today - timedelta(days=1))

with col_level:
    level = st.selectbox(
        "Agrégation",
        options=["Campagne", "Adset", "Publicité (ad)"],
        index=0,
    )


# ── Requête SQL principale ────────────────────────────────────────────────────

@st.cache_data(ttl=300)  # cache 5 min pour éviter les requêtes répétées
def load_data(since: str, until: str) -> pd.DataFrame:
    """
    Jointure entre ad_spend et les ventes Systeme.io.
    La jointure se fait sur utm_content = ad_id (niveau ad).
    utm_campaign = campaign_id est utilisé en fallback.
    """
    sql = """
        SELECT
            s.date,
            s.campaign_id,
            s.campaign_name,
            s.adset_id,
            s.adset_name,
            s.ad_id,
            s.ad_name,
            s.spend,
            s.impressions,
            s.clicks,
            s.meta_purchases,
            s.meta_revenue,
            COALESCE(sys.real_purchases, 0)     AS real_purchases,
            COALESCE(sys.real_revenue, 0)        AS real_revenue
        FROM ad_spend s
        LEFT JOIN (
            SELECT
                utm_content                       AS ad_id,
                COUNT(*)                          AS real_purchases,
                SUM(amount)                       AS real_revenue
            FROM sales
            WHERE date(created_at) BETWEEN ? AND ?
              AND utm_content != ''
              AND utm_content IS NOT NULL
            GROUP BY utm_content
        ) sys ON sys.ad_id = s.ad_id
        WHERE s.date BETWEEN ? AND ?
    """
    conn = db.get_connection()
    df = pd.read_sql_query(sql, conn, params=(since, until, since, until))
    conn.close()
    return df


# ── Chargement et transformation ──────────────────────────────────────────────

db.init_db()

since_str = date_since.isoformat()
until_str = date_until.isoformat()

df_raw = load_data(since_str, until_str)

if df_raw.empty:
    st.warning(
        "Aucune donnée disponible pour cette période. "
        "Lance `python sync_meta.py` pour synchroniser les insights Meta."
    )
    st.stop()

# Colonnes d'agrégation selon le niveau choisi
LEVEL_GROUPS = {
    "Campagne":        ["campaign_id", "campaign_name"],
    "Adset":           ["campaign_id", "campaign_name", "adset_id", "adset_name"],
    "Publicité (ad)":  ["campaign_id", "campaign_name", "adset_id", "adset_name", "ad_id", "ad_name"],
}

group_cols = LEVEL_GROUPS[level]

df = (
    df_raw.groupby(group_cols, as_index=False)
    .agg(
        spend=("spend", "sum"),
        impressions=("impressions", "sum"),
        clicks=("clicks", "sum"),
        meta_purchases=("meta_purchases", "sum"),
        meta_revenue=("meta_revenue", "sum"),
        real_purchases=("real_purchases", "sum"),
        real_revenue=("real_revenue", "sum"),
    )
)

# Calcul des métriques dérivées
df["roas_meta"] = df.apply(
    lambda r: round(r["meta_revenue"] / r["spend"], 2) if r["spend"] > 0 else 0, axis=1
)
df["roas_reel"] = df.apply(
    lambda r: round(r["real_revenue"] / r["spend"], 2) if r["spend"] > 0 else 0, axis=1
)
df["ecart_attribution"] = df.apply(
    lambda r: round((r["roas_reel"] - r["roas_meta"]) / r["roas_meta"] * 100, 1)
    if r["roas_meta"] > 0 else None,
    axis=1,
)
df["cpc"] = df.apply(
    lambda r: round(r["spend"] / r["clicks"], 2) if r["clicks"] > 0 else 0, axis=1
)


# ── KPIs globaux ──────────────────────────────────────────────────────────────
st.markdown("---")
k1, k2, k3, k4, k5 = st.columns(5)

total_spend = df["spend"].sum()
total_real_rev = df["real_revenue"].sum()
total_meta_rev = df["meta_revenue"].sum()
roas_global_reel = round(total_real_rev / total_spend, 2) if total_spend > 0 else 0
roas_global_meta = round(total_meta_rev / total_spend, 2) if total_spend > 0 else 0

k1.metric("💸 Dépense totale", f"{total_spend:,.2f} €")
k2.metric("💰 Revenu réel (Systeme.io)", f"{total_real_rev:,.2f} €")
k3.metric("📈 ROAS réel", f"{roas_global_reel}x")
k4.metric("🤖 ROAS Meta (pixel)", f"{roas_global_meta}x")

ecart_global = round((roas_global_reel - roas_global_meta) / roas_global_meta * 100, 1) if roas_global_meta > 0 else 0
k5.metric(
    "⚖️ Écart attribution",
    f"{ecart_global:+.1f}%",
    delta=f"{ecart_global:+.1f}%",
    delta_color="normal",
)

st.markdown("---")


# ── Tableau détaillé ──────────────────────────────────────────────────────────

# Colonnes affichées selon le niveau
name_col = {
    "Campagne":       "campaign_name",
    "Adset":          "adset_name",
    "Publicité (ad)": "ad_name",
}[level]

display_df = df[[
    name_col, "spend", "impressions", "clicks",
    "meta_purchases", "meta_revenue",
    "real_purchases", "real_revenue",
    "roas_meta", "roas_reel", "ecart_attribution",
]].copy()

display_df.columns = [
    "Nom", "Dépense (€)", "Impressions", "Clics",
    "Achats Meta (pixel)", "Revenu Meta (€)",
    "Achats réels", "Revenu réel (€)",
    "ROAS Meta", "ROAS Réel", "Écart (%)",
]

# Couleur conditionnelle : ROAS réel vs Meta
def color_ecart(val):
    if pd.isna(val):
        return ""
    color = "#d4edda" if val >= 0 else "#f8d7da"
    return f"background-color: {color}"

styled = (
    display_df.style
    .format({
        "Dépense (€)": "{:,.2f}",
        "Revenu Meta (€)": "{:,.2f}",
        "Revenu réel (€)": "{:,.2f}",
        "ROAS Meta": "{:.2f}x",
        "ROAS Réel": "{:.2f}x",
        "Écart (%)": lambda v: f"{v:+.1f}%" if pd.notna(v) else "—",
    })
    .applymap(color_ecart, subset=["Écart (%)"])
    .bar(subset=["Dépense (€)"], color="#aed6f1")
    .bar(subset=["ROAS Réel"], color="#a9dfbf")
)

st.subheader(f"Détail par {level.lower()}")
st.dataframe(styled, use_container_width=True, height=420)


# ── Graphique ROAS réel vs ROAS Meta ─────────────────────────────────────────
st.subheader("ROAS Réel vs ROAS Meta (Pixel)")

chart_df = df_raw.groupby("date", as_index=False).agg(
    spend=("spend", "sum"),
    meta_revenue=("meta_revenue", "sum"),
    real_revenue=("real_revenue", "sum"),
)
chart_df["ROAS Meta"] = chart_df.apply(
    lambda r: r["meta_revenue"] / r["spend"] if r["spend"] > 0 else 0, axis=1
)
chart_df["ROAS Réel"] = chart_df.apply(
    lambda r: r["real_revenue"] / r["spend"] if r["spend"] > 0 else 0, axis=1
)
chart_df = chart_df.set_index("date")[["ROAS Meta", "ROAS Réel"]]

st.line_chart(chart_df)


# ── Ventes sans UTM / non attribuées ─────────────────────────────────────────
with st.expander("🔍 Ventes Systeme.io non attribuées (utm_content vide)"):
    sql_unattr = """
        SELECT sale_id, email, amount, currency, created_at,
               utm_source, utm_campaign, utm_medium, utm_content
        FROM sales
        WHERE date(created_at) BETWEEN ? AND ?
          AND (utm_content IS NULL OR utm_content = '')
        ORDER BY created_at DESC
        LIMIT 100
    """
    conn = db.get_connection()
    df_unattr = pd.read_sql_query(sql_unattr, conn, params=(since_str, until_str))
    conn.close()

    if df_unattr.empty:
        st.success("Toutes les ventes de la période ont un utm_content.")
    else:
        st.warning(
            f"{len(df_unattr)} ventes sans utm_content — "
            "vérifier la convention UTM dans Ads Manager."
        )
        st.dataframe(df_unattr, use_container_width=True)


# ── Pied de page ──────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "Données : Meta Ads API (pixel) × Systeme.io (webhook). "
    "Jointure sur utm_content = ad_id. "
    f"Période : {since_str} → {until_str}."
)

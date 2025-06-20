import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ─────────────────────────────────────────────────────────────
# 1. CSV export links (public)
# ─────────────────────────────────────────────────────────────
RESP_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1uFynRj2NtaVZveKygfEuliuLYwsKe2zCjycjS5F-YPQ"
    "/export?format=csv&gid=341334397"
)
KSH_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1uFynRj2NtaVZveKygfEuliuLYwsKe2zCjycjS5F-YPQ"
    "/export?format=csv&gid=554598115"
)

# ─────────────────────────────────────────────────────────────
# 2. Load & merge (cache 10s)
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=10, show_spinner="Loading data…")
def load_data():
    resp = pd.read_csv(RESP_URL).rename(columns=str.strip)
    ksh  = pd.read_csv(KSH_URL).rename(columns=str.strip)
    return resp.merge(
        ksh,
        left_on="Kshetra",
        right_on="Kshetra Group",
        how="left"
    )

try:
    df = load_data()
except Exception as e:
    st.error(f"❌ Failed to load data: {e}")
    st.stop()

# ─────────────────────────────────────────────────────────────
# 3. Compute aggregates
# ─────────────────────────────────────────────────────────────
COL_STATE     = "Main Group"
COL_REGION    = "Kshetra"
COL_WORKER    = "Karyakarta Name_2"
COL_WORKER_ID = "Karyakarta ID"

# Total Donors
total_donors = len(df)

# State totals
state_totals = (
    df.groupby(COL_STATE).size()
      .reset_index(name="Registrations")
      .sort_values("Registrations", ascending=False)
)

# All region totals (for compact chart)
region_totals = (
    df.groupby([COL_STATE, COL_REGION]).size()
      .reset_index(name="Count")
      .sort_values("Count", ascending=False)
)
region_totals["Label"] = region_totals[COL_STATE] + " - " + region_totals[COL_REGION]

# Top 10 karyakartas for marquee
worker_totals = (
    df.groupby([COL_WORKER_ID, COL_WORKER]).size()
      .reset_index(name="Registrations")
      .sort_values("Registrations", ascending=False)
)
top10_workers = worker_totals.head(10)

# ─────────────────────────────────────────────────────────────
# 4. Streamlit UI
# ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="MBDD Leaderboard", layout="wide", page_icon="🩸")

# — Hero KPI for Total Donors
st.markdown(
    "<div style='background:#e0f7fa;padding:20px;border-radius:8px;text-align:center;'>"
    f"<h2>Total Donors Registered</h2>"
    f"<h1 style='font-size:48px;margin:0;'>{total_donors:,}</h1>"
    "</div>",
    unsafe_allow_html=True
)

st.markdown("## 🏆 Top 3 States")
cols = st.columns(3)
for i, (_, row) in enumerate(state_totals.head(3).iterrows()):
    medal = ["🥇","🥈","🥉"][i]
    cols[i].metric(
        label=f"{medal} {row[COL_STATE]}",
        value=f"{row['Registrations']:,} regs"
    )

st.markdown("---")

# — Compact Bar Chart of All Regions, colored by State
st.markdown("## 🌐 All Regions by Registrations")
fig = px.bar(
    region_totals,
    x="Label",
    y="Count",
    color=COL_STATE,
    labels={"Count":"Registrations", "Label":"Region"},
    title="",
)
fig.update_layout(
    height=400,
    xaxis_tickangle=-45,
    margin=dict(l=40,r=20,t=30,b=120),
    showlegend=True
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# — Marquee for Top 10 Karyakartas
ticker = "  |  ".join(
    f"{r[COL_WORKER_ID]} – {r[COL_WORKER]} ({r['Registrations']})"
    for _, r in top10_workers.iterrows()
)
st.markdown(f"""
<div style="overflow:hidden; white-space:nowrap; background:#fff3e0; padding:10px; border-radius:5px;">
  <marquee behavior="scroll" scrollamount="5" style="font-size:18px;">
    🌟 Top Karyakartas: {ticker}
  </marquee>
</div>
""", unsafe_allow_html=True)

st.markdown("_May the best state and team win!_ 🎉")

import streamlit as st
import pandas as pd
from datetime import datetime

# ─── 1. CSV URLs ───────────────────────────────────────────────────────────
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

# ─── 2. Load & merge (cached 10 s) ─────────────────────────────────────────
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

# ─── 3. Column names & aggregates ──────────────────────────────────────────
COL_STATE   = "Main Group"
COL_REGION  = "Kshetra"
COL_WORKER  = "Karyakarta Name_2"
COL_WORKER_ID = "Karyakarta ID"

# Total donors
total_donors = len(df)

# State totals
state_totals = (
    df.groupby(COL_STATE).size()
      .reset_index(name="Registrations")
      .sort_values("Registrations", ascending=False)
)

# Region totals
region_totals = (
    df.groupby([COL_STATE, COL_REGION]).size()
      .reset_index(name="Count")
)

# Worker totals overall (for marquee)
worker_totals = (
    df.groupby([COL_WORKER_ID, COL_WORKER]).size()
      .reset_index(name="Registrations")
      .sort_values("Registrations", ascending=False)
)

# ─── 4. Identify leading state ────────────────────────────────────────────
lead_state = state_totals.iloc[0][COL_STATE]
lead_count = int(state_totals.iloc[0]["Registrations"])

# Top 3 states
top3 = state_totals.head(3)

# Top 10 karyakartas for ticker
top10 = worker_totals.head(10)

# Regions in leading state
lead_regions = (
    region_totals[region_totals[COL_STATE] == lead_state]
    .sort_values("Count", ascending=False)
)

# All regions across all states (prefixed)
all_regions = region_totals.copy()
all_regions["Label"] = (
    all_regions[COL_STATE] + " - " + all_regions[COL_REGION]
)
all_regions = all_regions.sort_values("Count", ascending=False)

# ─── 5. Build UI ──────────────────────────────────────────────────────────
st.set_page_config(page_title="MBDD Leaderboard", layout="wide", page_icon="🩸")

# Hero banner for leading state
st.markdown(f"""
<div style="
  padding: 20px;
  background: linear-gradient(90deg,#ff9a9e,#fad0c4);
  border-radius: 10px;
  text-align:center;
  font-size:24px;
  color:#333;
">
  🏆 Leading State: <strong>{lead_state}</strong>
  with <strong>{lead_count}</strong> registrations!
</div>
""", unsafe_allow_html=True)

st.markdown(f"**Total Donors Registered:** {total_donors:,}")

st.markdown("---")

# Top 3 States
st.subheader("🥇 Top 3 States")
cols = st.columns(3)
medals = ["🥇","🥈","🥉"]
for i, (_, row) in enumerate(top3.iterrows()):
    cols[i].metric(f"{medals[i]} {row[COL_STATE]}", f"{int(row['Registrations']):,}")

st.markdown("---")

# Bar chart of all states
st.subheader("📊 Registrations by State")
st.bar_chart(
    state_totals.set_index(COL_STATE)["Registrations"],
    use_container_width=True
)

st.markdown("---")

# Regions in leading state
st.subheader(f"🗺️ Regions in {lead_state}")
st.bar_chart(
    lead_regions.set_index(COL_REGION)["Count"],
    use_container_width=True
)

st.markdown("---")

# All regions across all states
st.subheader("🌐 All Regions (by Registrations)")
st.bar_chart(
    all_regions.set_index("Label")["Count"],
    use_container_width=True
)

st.markdown("---")

# Marquee ticker for top 10 workers
ticker_text = "  |  ".join(
    f"{row[COL_WORKER_ID]} – {row[COL_WORKER]} ({row['Registrations']})"
    for _, row in top10.iterrows()
)
st.markdown(f"""
<div style="overflow:hidden; white-space:nowrap;">
  <marquee behavior="scroll" scrollamount="6" style="font-size:18px;">
    🌟 Top Karyakartas: {ticker_text}
  </marquee>
</div>
""", unsafe_allow_html=True)

st.markdown("---")
st.markdown("_May the best state (and region, and karyakarta) win!_ 🎉")

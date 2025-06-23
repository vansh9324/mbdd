import streamlit as st
import pandas as pd
from datetime import datetime

# CSV URLs for public Google Sheets
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

@st.cache_data(ttl=15)
def load_data():
    resp = pd.read_csv(RESP_URL).rename(columns=str.strip)
    ksh  = pd.read_csv(KSH_URL).rename(columns=str.strip)

    # Force string type to avoid dtype mismatch
    resp["Kshetra"] = resp["Kshetra"].astype(str).str.strip()
    ksh["Kshetra Group"] = ksh["Kshetra Group"].astype(str).str.strip()

    return resp.merge(ksh, left_on="Kshetra", right_on="Kshetra Group", how="left")

try:
    df = load_data()
except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()

# 3. Aggregations
STATE      = "Main Group"
REGION     = "Kshetra"
WORKER     = "Karyakarta Name_2"
WORKER_ID  = "Karyakarta ID"

total_donors  = len(df)
state_totals  = (
    df.groupby(STATE).size()
      .reset_index(name="Registrations")
      .sort_values("Registrations", ascending=False)
)
region_totals = (
    df.groupby(REGION).size()
      .reset_index(name="Registrations")
      .sort_values("Registrations", ascending=False)
)
top_workers   = (
    df.groupby([WORKER_ID, WORKER]).size()
      .reset_index(name="Registrations")
      .sort_values("Registrations", ascending=False)
      .head(10)
)

# 4. UI
st.set_page_config(page_title="MBDD Leaderboard", layout="wide", page_icon="🩸")

# --- Dark theme CSS overrides
st.markdown("""
    <style>
      /* Page background */
      .stApp { background-color: #1e1e2e; color: #fff; }
      /* DataFrame text */
      .stDataFrame table { color: #000 !important; }
    </style>
""", unsafe_allow_html=True)

# Heading
st.markdown("<h1 style='text-align:center;color:#ffa600;'>🩸 MBDD – Mega Blood Donation Drive</h1>", unsafe_allow_html=True)

# Total donors card
st.markdown(f"""
<div style="
  display:inline-block;
  background:#003f5c;
  color:#fff;
  padding:15px 25px;
  border-radius:8px;
  margin-bottom:20px;
">
  <div style="font-size:14px;opacity:0.8;">Total Donors</div>
  <div style="font-size:36px;font-weight:bold;color:#ffa600;">{total_donors:,}</div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Top 3 States
st.markdown("<h2 style='color:#ffa600;'>🏆 Top 3 States</h2>", unsafe_allow_html=True)
cols = st.columns(3)
medals = ["🥇","🥈","🥉"]
for i, row in enumerate(state_totals.head(3).itertuples(index=False)):
    cols[i].markdown(f"""
      <div style="
        background:#2f4b7c;
        padding:20px;
        border-radius:8px;
        text-align:center;
        color:#fff;
      ">
        <div style="font-size:20px;font-weight:bold;">{row[STATE]}</div>
        <div style="font-size:28px;color:#ffa600;font-weight:bold;">
          {row['Registrations']:,}
        </div>
        <div style="font-size:12px;opacity:0.8;">Total Registrations</div>
      </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Bar chart: all states
st.markdown("<h2 style='color:#ffa600;'>📊 Registrations by State</h2>", unsafe_allow_html=True)
st.bar_chart(state_totals.set_index(STATE)["Registrations"], use_container_width=True)

st.markdown("---")

# Bar chart: all kshetras
st.markdown("<h2 style='color:#ffa600;'>🗺️ Registrations by Kshetra</h2>", unsafe_allow_html=True)
st.bar_chart(region_totals.set_index(REGION)["Registrations"], use_container_width=True)

st.markdown("---")

# Marquee for Top 10 Karyakartas
ticker = "  |  ".join(
    f"<span style='color:#ffa600;'>{r[WORKER_ID]}</span> – {r[WORKER]} ({r['Registrations']:,})"
    for _, r in top_workers.iterrows()
)
st.markdown(f"""
<div style="
  background:#000;
  color:#fff;
  padding:10px;
  border-radius:5px;
  overflow:hidden;
  white-space:nowrap;
">
  <marquee behavior="scroll" scrollamount="5" style="font-size:18px;">
    🌟 Top Karyakartas: {ticker}
  </marquee>
</div>
""", unsafe_allow_html=True)

st.markdown("<p style='text-align:center;opacity:0.7;'>_May the best state win!_ 🎉</p>", unsafe_allow_html=True)

# Auto-refresh every 10s
st.markdown("<script>setTimeout(()=>{window.location.reload();},10000);</script>", unsafe_allow_html=True)

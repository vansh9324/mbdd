import streamlit as st
import pandas as pd
from datetime import datetime

# ─── 1. CSV links (public) ───────────────────────────────────────────────
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

# ─── 2. Load & merge (cache 10s) ─────────────────────────────────────────
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

# ─── 3. Rename & compute aggregates ────────────────────────────────────────
COL_STATE    = "Main Group"
COL_REGION   = "Kshetra"
COL_WORKER   = "Karyakarta Name_2"
COL_WORKER_ID = "Karyakarta ID"

# Total donors
total_donors = len(df)

# State totals
state_totals = (
    df.groupby(COL_STATE).size()
      .reset_index(name="Registrations")
      .sort_values("Registrations", ascending=False)
)

# Top 5 karyakartas overall (ID + Name)
top5 = (
    df.groupby([COL_WORKER_ID, COL_WORKER])["Kshetra"]
      .count()
      .reset_index(name="Registrations")
      .sort_values("Registrations", ascending=False)
      .head(5)
)

# Per-state top region + worker
region_totals = (
    df.groupby([COL_STATE, COL_REGION]).size()
      .reset_index(name="Count")
)
worker_totals = (
    df.groupby([COL_STATE, COL_REGION, COL_WORKER_ID, COL_WORKER]).size()
      .reset_index(name="Count")
)

summary = []
for _, row in state_totals.iterrows():
    st_name = row[COL_STATE]
    # top region
    top_reg = region_totals[region_totals[COL_STATE] == st_name] \
                .nlargest(1, "Count").iloc[0]
    # top worker in that region
    top_wrk = worker_totals[
                (worker_totals[COL_STATE] == st_name) &
                (worker_totals[COL_REGION] == top_reg[COL_REGION])
              ].nlargest(1, "Count").iloc[0]
    summary.append({
        "State": st_name,
        "Registrations": int(row["Registrations"]),
        "Top Region": top_reg[COL_REGION],
        "Region Count": int(top_reg["Count"]),
        "Top Worker": f"{top_wrk[COL_WORKER_ID]} – {top_wrk[COL_WORKER]}",
        "Worker Count": int(top_wrk["Count"]),
    })
summary_df = pd.DataFrame(summary)

# ─── 4. Build the Streamlit UI ────────────────────────────────────────────
st.set_page_config(page_title="MBDD Leaderboard", layout="wide", page_icon="🩸")

# Header
st.markdown("<h1 style='text-align:center;'>🩸 MBDD Live Leaderboard</h1>", unsafe_allow_html=True)
col1, col2 = st.columns([3,1])
with col1:
    st.metric("Total Donors Registered", total_donors)
with col2:
    if st.button("🔄 Refresh"):
        st.cache_data.clear()
        df = load_data()

st.markdown("---")

# Top 3 States
st.subheader("🏆 Top 3 States")
top3 = state_totals.head(3)
cols = st.columns(3)
for i, (_, r) in enumerate(top3.iterrows()):
    medal = ["🥇","🥈","🥉"][i]
    cols[i].metric(f"{medal} {r[COL_STATE]}", int(r["Registrations"]))

st.markdown("---")

# State Bar Chart
st.subheader("📊 Registrations by State")
st.bar_chart(state_totals.set_index(COL_STATE)["Registrations"], use_container_width=True)

st.markdown("---")

# Top 5 Karyakartas
st.subheader("👤 Top 5 Karyakartas")
st.bar_chart(
    top5.assign(Label=top5[COL_WORKER_ID] + ": " + top5[COL_WORKER])
        .set_index("Label")["Registrations"], 
    use_container_width=True
)

st.markdown("---")

# Detailed Summary Table
st.subheader("🗺️ State → Region → Top Worker")
st.dataframe(summary_df, use_container_width=True)

st.markdown("***")
st.markdown("_May the best state win!_ 🎉")

import streamlit as st
import pandas as pd
import altair as alt       #  ← new import
from datetime import datetime
import streamlit.components.v1 as components

# ─────────────────────────────────────────
# 1.  Google-Sheets CSV links
# ─────────────────────────────────────────
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

    resp["Kshetra"]       = resp["Kshetra"].astype(str).str.strip()
    ksh["Kshetra Group"]  = ksh["Kshetra Group"].astype(str).str.strip()

    return resp.merge(ksh, left_on="Kshetra",
                           right_on="Kshetra Group", how="left")

try:
    df = load_data()
except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()

# ─────────────────────────────────────────
# 2.  Aggregations
# ─────────────────────────────────────────
STATE, REGION = "Main Group", "Kshetra"
WORKER, WID   = "Karyakarta Name_2", "Karyakarta ID"

total_donors = len(df)

state_totals = (df.groupby(STATE).size()
                  .reset_index(name="Registrations")
                  .sort_values("Registrations", ascending=False))
# drop rows where Kshetra is NaN or empty after stripping
df = df[ df[REGION].str.strip().str.lower().ne('nan') & df[REGION].str.strip().ne('') ]
region_totals = (df.groupby(REGION).size()
                   .reset_index(name="Registrations")
                   .sort_values("Registrations", ascending=False))

top_workers = (df.groupby([WID, WORKER]).size()
                 .reset_index(name="Registrations")
                 .sort_values("Registrations", ascending=False)
                 .head(10))

# ── NEW: top karyakarta per kshetra ──
top_by_ksh = (df.groupby([REGION, WORKER])
                .size()
                .reset_index(name="Count")
                .sort_values(["Kshetra", "Count"], ascending=[True, False])
                .drop_duplicates(REGION)
                .rename(columns={WORKER: "Top Karyakarta"}))[ [REGION, "Top Karyakarta"] ]

region_totals = region_totals.merge(top_by_ksh, on=REGION, how="left")

# ─────────────────────────────────────────
# 3.  UI  (unchanged styling)
# ─────────────────────────────────────────
st.set_page_config(page_title="MBDD Leaderboard",
                   layout="wide", page_icon="🩸")

st.markdown("""
<style>
  .stApp { background:#1e1e2e; color:#fff; }
  .stDataFrame table { color:#000 !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center;color:#ffa600;'>🩸 MBDD – Mega Blood Donation Drive</h1>",
            unsafe_allow_html=True)

st.markdown(f"""
<div style="display:inline-block;background:#003f5c;color:#fff;
            padding:15px 25px;border-radius:8px;margin-bottom:20px;">
  <div style="font-size:14px;opacity:0.8;">Total Donors</div>
  <div style="font-size:36px;font-weight:bold;color:#ffa600;">{total_donors:,}</div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ── Top-3 state cards (bug-free)
st.markdown("<h2 style='color:#ffa600;'>🏆 Top 3 States</h2>", unsafe_allow_html=True)
cols = st.columns(3)
for col, (state_name, count) in zip(cols,
        state_totals.head(3).itertuples(index=False, name=None)):
    col.markdown(f"""
      <div style="background:#2f4b7c;padding:20px;border-radius:8px;
                  text-align:center;color:#fff;">
        <div style="font-size:20px;font-weight:bold;">{state_name}</div>
        <div style="font-size:28px;color:#ffa600;font-weight:bold;">{count:,}</div>
        <div style="font-size:12px;opacity:0.8;">Total Registrations</div>
      </div>
    """, unsafe_allow_html=True)

st.markdown("---")

st.markdown("<h2 style='color:#ffa600;'>📊 Registrations by State</h2>", unsafe_allow_html=True)
st.bar_chart(state_totals.set_index(STATE)["Registrations"], use_container_width=True)

st.markdown("---")

# ─────────────────────────────────────────
# 4.  NEW Altair chart for Kshetra
# ─────────────────────────────────────────
st.markdown("<h2 style='color:#ffa600;'>🗺️ Registrations by Kshetra</h2>",
            unsafe_allow_html=True)

ks_chart = (alt.Chart(region_totals)
    .mark_bar()
    .encode(
        x=alt.X("Registrations:Q", title="Registrations"),
        y=alt.Y("Kshetra:N", sort="-x", title="Kshetra"),
        color=alt.value("#ffa600"),
        tooltip=[
            alt.Tooltip("Kshetra:N",           title="Kshetra"),
            alt.Tooltip("Registrations:Q",     title="Registrations"),
            alt.Tooltip("Top Karyakarta:N",    title="Top Karyakarta")
        ]
    )
    .properties(height=200)
)
st.altair_chart(ks_chart, use_container_width=True)

st.markdown("---")

# ── Marquee Top-10 workers
ticker = "  |  ".join(
    f"<span style='color:#ffa600;'>{r[WID]}</span> – {r[WORKER]} ({r['Registrations']:,})"
    for _, r in top_workers.iterrows()
)
st.markdown(f"""
<div style="background:#000;color:#fff;padding:10px;border-radius:5px;
            overflow:hidden;white-space:nowrap;">
  <marquee scrollamount="5" style="font-size:18px;">
    🌟 Top Karyakartas: {ticker}
  </marquee>
</div>
""", unsafe_allow_html=True)

st.markdown("<p style='text-align:center;opacity:0.7;'>_May the best state win!_ 🎉</p>",
            unsafe_allow_html=True)

# Auto-refresh
st.markdown("<script>setTimeout(()=>{window.location.reload();},10000);</script>",
            unsafe_allow_html=True)

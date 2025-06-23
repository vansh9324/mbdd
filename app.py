import streamlit as st
import pandas as pd
import altair as alt
import streamlit.components.v1 as components
from datetime import datetime

# ───────── 1.  CSV links  ───────────────────────────────────────────
RESP_URL = (
    "https://docs.google.com/spreadsheets/d/1uFynRj2NtaVZveKygfEuliuLYwsKe2zCjycjS5F-YPQ"
    "/export?format=csv&gid=341334397"
)
KSH_URL = (
    "https://docs.google.com/spreadsheets/d/1uFynRj2NtaVZveKygfEuliuLYwsKe2zCjycjS5F-YPQ"
    "/export?format=csv&gid=554598115"
)

@st.cache_data(ttl=15)
def load_data() -> pd.DataFrame:
    resp = pd.read_csv(RESP_URL).rename(columns=str.strip)
    ksh  = pd.read_csv(KSH_URL ).rename(columns=str.strip)

    resp["Kshetra"]       = resp["Kshetra"].astype(str).str.strip()
    ksh ["Kshetra Group"] = ksh ["Kshetra Group"].astype(str).str.strip()

    df = resp.merge(ksh, left_on="Kshetra", right_on="Kshetra Group", how="left")

    # drop rows where Kshetra is blank/NaN after stripping
    df = df[df["Kshetra"].str.strip().ne("") & df["Kshetra"].str.lower().ne("nan")]
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()

# ───────── 2.  Aggregations  ────────────────────────────────────────
STATE, REGION = "Main Group", "Kshetra"
WORKER, WID   = "Karyakarta Name_2", "Karyakarta ID"

total_regs = len(df)

state_tot = (df.groupby(STATE).size()
               .reset_index(name="Registrations")
               .sort_values("Registrations", ascending=False))

#region totals with top karyakarta
top_by_ksh = (df.groupby([REGION, WORKER])
                .size()
                .reset_index(name="Count")
                .sort_values(["Kshetra", "Count"], ascending=[True, False])
                .drop_duplicates(REGION)
                .rename(columns={WORKER: "Top Karyakarta"}))[ [REGION, "Top Karyakarta"] ]

ks_tot = (df.groupby(REGION).size()
            .reset_index(name="Registrations")
            .sort_values("Registrations", ascending=False)
            .merge(top_by_ksh, on=REGION, how="left"))

top10_workers = (df.groupby([WORKER, WID]).size()
                   .reset_index(name="Registrations")
                   .sort_values("Registrations", ascending=False)
                   .head(10))

# ───────── 3.  Page scaffold & theme  ───────────────────────────────
st.set_page_config("MBDD Leaderboard", "🩸", layout="wide")

st.markdown("""
<style>
 .stApp {background:#1e1e2e;color:#fff;}
 .stDataFrame table {color:#000 !important;}
</style>""", unsafe_allow_html=True)

st.markdown(
    "<h1 style='text-align:center;color:#ffa600;'>🩸 MBDD – Mega Blood Donation Drive</h1>",
    unsafe_allow_html=True)

# total-registrations pill
st.markdown(f"""
<div style="display:inline-block;background:#003f5c;padding:14px 24px;
            border-radius:8px;margin-bottom:18px;color:#fff;">
  <div style="font-size:14px;opacity:0.8;">Total Donors</div>
  <div style="font-size:34px;font-weight:bold;color:#ffa600;">{total_regs:,}</div>
</div>""", unsafe_allow_html=True)

st.markdown("---")

# ───────── 4.  Top-3 States cards  ─────────────────────────────────
st.markdown("<h2 style='color:#ffa600;'>🏆 Top 3 States</h2>", unsafe_allow_html=True)
cards = st.columns(3)
for card, (state, regs) in zip(cards, state_tot.head(3).itertuples(index=False, name=None)):
    card.markdown(f"""
    <div style="background:#2f4b7c;padding:20px;border-radius:8px;text-align:center;color:#fff;">
      <div style="font-size:20px;font-weight:bold;">{state}</div>
      <div style="font-size:28px;color:#ffa600;font-weight:bold;">{regs:,}</div>
      <div style="font-size:12px;opacity:0.8;">Total Registrations</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# ───────── 5.  Side-by-side charts  ────────────────────────────────
left, right = st.columns(2)

with left:
    st.markdown("<h3 style='color:#ffa600;'>📊 Registrations by State</h3>",
                unsafe_allow_html=True)
    st.bar_chart(state_tot.set_index(STATE)["Registrations"], use_container_width=True)

with right:
    st.markdown("<h3 style='color:#ffa600;'>🗺️ Registrations by Kshetra</h3>",
                unsafe_allow_html=True)
    ks_chart = (alt.Chart(ks_tot)
        .mark_bar(color="#ffa600")
        .encode(
            x=alt.X("Registrations:Q", title="Regs"),
            y=alt.Y("Kshetra:N", sort="-x", title="Kshetra"),
            tooltip=[
                alt.Tooltip("Kshetra:N", title="Kshetra"),
                alt.Tooltip("Registrations:Q", title="Registrations"),
                alt.Tooltip("Top Karyakarta:N", title="Top Karyakarta")
            ])
        .properties(height=500))
    st.altair_chart(ks_chart, use_container_width=True)

st.markdown("---")

# ───────── 6.  Marquee Top-10 workers  ─────────────────────────────
ticker_html = " | ".join(
    f"<span style='color:#ffa600;font-weight:bold;'>{r[WORKER]}</span>"
    f"<span style='color:#aaa;'> (ID:{r[WID]})</span> "
    f"- {r['Registrations']} regs"
    for _, r in top10_workers.iterrows()
)
components.html(f"""
<div style="background:#000;color:#fff;padding:10px;border-radius:5px;overflow:hidden;">
  <marquee scrollamount="5" style="font-size:18px;">
    🌟 Top Karyakartas: {ticker_html}
  </marquee>
</div>""", height=55)

st.markdown("<p style='text-align:center;opacity:0.7;'>_May the best state win!_ 🎉</p>",
            unsafe_allow_html=True)

# auto-refresh
st.markdown("<script>setTimeout(()=>{window.location.reload()},10000);</script>",
            unsafe_allow_html=True)

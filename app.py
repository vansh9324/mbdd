import streamlit as st
import pandas as pd
from datetime import datetime

# ── DIRECT CSV LINKS (verified in your browser) ─────────────────────
RESP_URL = (
    "https://docs.google.com/spreadsheets/d/1uFynRj2NtaVZveKygfEuliuLYwsKe2zCjycjS5F-YPQ"
    "/export?format=csv&gid=341334397"    # Form Responses 1
)
KSH_URL = (
    "https://docs.google.com/spreadsheets/d/1uFynRj2NtaVZveKygfEuliuLYwsKe2zCjycjS5F-YPQ"
    "/export?format=csv&gid=554598115"    # Kshetra
)

# ── LOAD & MERGE (cached 10 s) ──────────────────────────────────────
@st.cache_data(ttl=10, show_spinner="Fetching Google Sheets …")
def load_data():
    resp = pd.read_csv(RESP_URL)
    ksh  = pd.read_csv(KSH_URL)
    return resp.merge(
        ksh,
        left_on="Kshetra",
        right_on="Kshetra Group",
        how="left"
    )

try:
    df = load_data()
except Exception as e:
    st.error(f"❌ CSV fetch failed → {e}")
    st.stop()

# ── COLUMN ALIASES ─────────────────────────────────────────────────
COL_KSHTRA   = "Kshetra"
COL_MAIN     = "Main Group"
COL_REG_NAME = "Karyakarta Name_2"

# ── AGGREGATIONS ───────────────────────────────────────────────────
state_totals = (
    df.groupby(COL_MAIN).size()
      .reset_index(name="कुल रजिस्ट्रेशन")
      .sort_values("कुल रजिस्ट्रेशन", ascending=False)
)

kshetra_totals = (
    df.groupby([COL_MAIN, COL_KSHTRA]).size()
      .reset_index(name="रजिस्ट्रेशन")
)

karya_totals = (
    df.groupby([COL_MAIN, COL_KSHTRA, COL_REG_NAME]).size()
      .reset_index(name="रजिस्ट्रेशन")
)

rows = []
for _, r in state_totals.iterrows():
    state   = r[COL_MAIN]
    total   = int(r["कुल रजिस्ट्रेशन"])

    best_sub = (
        kshetra_totals[kshetra_totals[COL_MAIN] == state]
        .nlargest(1, "रजिस्ट्रेशन").iloc[0]
    )
    best_reg = (
        karya_totals[
            (karya_totals[COL_MAIN] == state) &
            (karya_totals[COL_KSHTRA] == best_sub[COL_KSHTRA])
        ]
        .nlargest(1, "रजिस्ट्रेशन").iloc[0]
    )

    rows.append({
        "राज्य": state,
        "कुल रजिस्ट्रेशन": total,
        "शीर्ष क्षेत्र": best_sub[COL_KSHTRA],
        "क्षेत्र रजिस्ट्रेशन": int(best_sub["रजिस्ट्रेशन"]),
        "शीर्ष कार्यकर्ता": best_reg[COL_REG_NAME],
        "कार्यकर्ता रजिस्ट्रेशन": int(best_reg["रजिस्ट्रेशन"]),
    })

board = pd.DataFrame(rows).sort_values("कुल रजिस्ट्रेशन", ascending=False)

# ── STREAMLIT UI ───────────────────────────────────────────────────
st.set_page_config(page_title="🩸 MBDD Live Leaderboard",
                   page_icon="🩸", layout="wide")

st.title("🩸  MBDD – Mega Blood Donation Drive")
st.caption(f"Last refresh  {datetime.now():%H:%M:%S}")

st.markdown("### 🏆 राज्य रैंकिंग")
st.dataframe(state_totals.rename(columns={COL_MAIN: "राज्य"}),
             hide_index=True, use_container_width=True)

st.markdown("### 🗺️  क्षेत्र व शीर्ष कार्यकर्ता")
st.dataframe(board, hide_index=True, use_container_width=True)

st.markdown("### 📊  बार चार्ट (राज्य-वार)")
st.bar_chart(state_totals.set_index(COL_MAIN)["कुल रजिस्ट्रेशन"])

if st.button("🔄 Manual refresh"):
    st.cache_data.clear()
    st.experimental_rerun()

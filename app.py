import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# public-share link (no /edit, no #gid)
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1uFynRj2NtaVZveKygfEuliuLYwsKe2zCjycjS5F-YPQ"

RESP_GID =341334397
KSH_GID  =554598115
conn: GSheetsConnection = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=10, show_spinner="Loading Google Sheets …")
def load_data():
    try:
        resp = conn.read(spreadsheet=SPREADSHEET_URL, worksheet=RESP_GID)
        ksh  = conn.read(spreadsheet=SPREADSHEET_URL, worksheet=KSH_GID)
        return resp, ksh
    except Exception as e:
        # bubble up so caller can handle
        raise RuntimeError(f"CSV fetch failed → {e}") from e

try:
    resp_df, ksh_df = load_data()
except Exception as err:
    st.error(str(err))
    st.stop()

# ── Merge & clean ─────────────────────────────────────────────
df = resp_df.merge(
        ksh_df,
        left_on="Kshetra",
        right_on="Kshetra Group",
        how="left"
)

# ── Aggregations ─────────────────────────────────────────────────────
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
    state = r[COL_MAIN]
    total = int(r["कुल रजिस्ट्रेशन"])
    best_sub = kshetra_totals[kshetra_totals[COL_MAIN] == state]\
               .nlargest(1, "रजिस्ट्रेशन").iloc[0]
    best_reg = karya_totals[
        (karya_totals[COL_MAIN] == state) &
        (karya_totals[COL_KSHTRA] == best_sub[COL_KSHTRA])
    ].nlargest(1, "रजिस्ट्रेशन").iloc[0]

    rows.append({
        "राज्य": state,
        "कुल रजिस्ट्रेशन": total,
        "शीर्ष क्षेत्र": best_sub[COL_KSHTRA],
        "क्षेत्र रजिस्ट्रेशन": int(best_sub["रजिस्ट्रेशन"]),
        "शीर्ष कार्यकर्ता": best_reg[COL_REG_NAME],
        "कार्यकर्ता रजिस्ट्रेशन": int(best_reg["रजिस्ट्रेशन"])
    })

board = pd.DataFrame(rows).sort_values("कुल रजिस्ट्रेशन", ascending=False)

# ── Streamlit UI ─────────────────────────────────────────────────────
st.set_page_config(page_title="🩸 MBDD Live Leaderboard",
                   page_icon="🩸", layout="wide")

st.title("🩸  MBDD – Mega Blood Donation Drive")
st.caption(f"Last refresh  {datetime.now():%H:%M:%S}  (auto 10 s)")

st.markdown("### 🏆 राज्य रैंकिंग")
st.dataframe(state_totals.rename(columns={COL_MAIN: "राज्य"}),
             hide_index=True, use_container_width=True)

st.markdown("### 🗺️  क्षेत्र व शीर्ष कार्यकर्ता")
st.dataframe(board, hide_index=True, use_container_width=True)

st.markdown("### 📊  बार चार्ट (राज्य-वार)")
st.bar_chart(state_totals.set_index(COL_MAIN)["कुल रजिस्ट्रेशन"])

if st.button("🔄 Refresh now"):
    st.cache_data.clear()
    st.experimental_rerun()

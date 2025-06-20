import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# ─────────────────────────────────────────────
# 1. Connect once (cached automatically)
# ─────────────────────────────────────────────
conn: GSheetsConnection = st.connection("gsheets", type=GSheetsConnection)

# 2. Read the two worksheets (with 10-s cache)
@st.cache_data(ttl=10)
def load_data():
    resp_df = conn.read(worksheet="Form Responses 1")        # donor rows
    ksh_df  = conn.read(worksheet="Kshetra")                 # mapping table
    return resp_df, ksh_df

resp_df, ksh_df = load_data()

# 3. Merge on Kshetra → Main Group
df = resp_df.merge(
    ksh_df,
    left_on="Kshetra",
    right_on="Kshetra Group",
    how="left",
)

# ───── column aliases
COL_KSHTRA   = "Kshetra"
COL_MAIN     = "Main Group"
COL_REG_NAME = "Karyakarta Name_2"

# 4. Aggregations
state_totals = (
    df.groupby(COL_MAIN)
      .size()
      .reset_index(name="कुल रजिस्ट्रेशन")
      .sort_values("कुल रजिस्ट्रेशन", ascending=False)
)

kshetra_totals = (
    df.groupby([COL_MAIN, COL_KSHTRA])
      .size()
      .reset_index(name="रजिस्ट्रेशन")
)

karya_totals = (
    df.groupby([COL_MAIN, COL_KSHTRA, COL_REG_NAME])
      .size()
      .reset_index(name="रजिस्ट्रेशन")
)

# Build summary board
rows = []
for _, r in state_totals.iterrows():
    state = r[COL_MAIN]
    total = int(r["कुल रजिस्ट्रेशन"])
    top_kshetra = (
        kshetra_totals[kshetra_totals[COL_MAIN] == state]
        .nlargest(1, "रजिस्ट्रेशन")
        .iloc[0]
    )
    top_karya = (
        karya_totals[
            (karya_totals[COL_MAIN] == state) &
            (karya_totals[COL_KSHTRA] == top_kshetra[COL_KSHTRA])
        ]
        .nlargest(1, "रजिस्ट्रेशन")
        .iloc[0]
    )
    rows.append({
        "राज्य": state,
        "कुल रजिस्ट्रेशन": total,
        "शीर्ष क्षेत्र": top_kshetra[COL_KSHTRA],
        "क्षेत्र रजिस्ट्रेशन": int(top_kshetra["रजिस्ट्रेशन"]),
        "शीर्ष कार्यकर्ता": top_karya[COL_REG_NAME],
        "कार्यकर्ता रजिस्ट्रेशन": int(top_karya["रजिस्ट्रेशन"]),
    })

board = pd.DataFrame(rows).sort_values("कुल रजिस्ट्रेशन", ascending=False)

# ─────────────────────────────────────────────
# 5. Streamlit UI
# ─────────────────────────────────────────────
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

if st.button("🔄 Refresh now"):
    st.cache_data.clear()
    st.experimental_rerun()

import streamlit as st
import pandas as pd
from datetime import datetime

# ─────────────────────────────────────────────────────────────
# 0. CSV export links (public “Anyone with link”)
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
# 1. Load & merge data (cached 10 s)
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=10, show_spinner="डेटा लोड हो रहा है…")
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
    st.error(f"❌ डेटा लोड में त्रुटि: {e}")
    st.stop()

# ─────────────────────────────────────────────────────────────
# 2. Compute metrics
# ─────────────────────────────────────────────────────────────
COL_MAIN     = "Main Group"
COL_KSHTRA   = "Kshetra"
COL_KARYA    = "Karyakarta Name_2"

# State totals
state_totals = (
    df.groupby(COL_MAIN)
      .size()
      .reset_index(name="कुल रजिस्ट्रेशन")
      .sort_values("कुल रजिस्ट्रेशन", ascending=False)
)

# Kshetra totals
kshetra_totals = (
    df.groupby([COL_MAIN, COL_KSHTRA])
      .size()
      .reset_index(name="रजिस्ट्रेशन")
)

# Karyakarta totals
karya_totals = (
    df.groupby([COL_MAIN, COL_KSHTRA, COL_KARYA])
      .size()
      .reset_index(name="रजिस्ट्रेशन")
)

# Build summary per-state
summary_rows = []
for _, st_row in state_totals.iterrows():
    state = st_row[COL_MAIN]
    total = int(st_row["कुल रजिस्ट्रेशन"])
    # top Kshetra
    top_ksh = (
        kshetra_totals[kshetra_totals[COL_MAIN] == state]
        .nlargest(1, "रजिस्ट्रेशन").iloc[0]
    )
    # top Karyakarta in that kshetra
    top_kr = (
        karya_totals[
            (karya_totals[COL_MAIN] == state) &
            (karya_totals[COL_KSHTRA] == top_ksh[COL_KSHTRA])
        ]
        .nlargest(1, "रजिस्ट्रेशन").iloc[0]
    )
    summary_rows.append({
        "राज्य": state,
        "कुल रजिस्ट्रेशन": total,
        "शीर्ष क्षेत्र": top_ksh[COL_KSHTRA],
        "क्षेत्र रेज़िस्ट्री": int(top_ksh["रजिस्ट्रेशन"]),
        "शीर्ष कार्यकर्ता": top_kr[COL_KARYA],
        "कार्यकर्ता रेज़िस्ट्री": int(top_kr["रजिस्ट्रेशन"]),
    })
summary_df = pd.DataFrame(summary_rows)

# ─────────────────────────────────────────────────────────────
# 3. Streamlit UI
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🩸 MBDD लाइव प्रतियोगिता",
    page_icon="🩸",
    layout="wide"
)

# Header
st.markdown(
    "<h1 style='text-align:center;'>🩸 MBDD – मैगा रक्त दान ड्राइव प्रतियोगिता</h1>",
    unsafe_allow_html=True
)
col_time, col_refresh = st.columns([3,1])
with col_time:
    st.markdown(f"**अद्यतन समय:** {datetime.now():%H:%M:%S}")
with col_refresh:
    if st.button("🔄 रिफ्रेश"):
        st.cache_data.clear()
        df = load_data()
        state_totals = (
            df.groupby(COL_MAIN).size()
              .reset_index(name="कुल रजिस्ट्रेशन")
              .sort_values("कुल रजिस्ट्रेशन", ascending=False)
        )
        summary_df = pd.DataFrame(summary_rows)  # rebuild if needed

st.markdown("---")

# Top 3 States as Metrics
st.markdown("## 🏅 शीर्ष 3 राज्य")
top3 = state_totals.head(3).reset_index(drop=True)
cols = st.columns(3)
medals = ["🥇", "🥈", "🥉"]
for i, row in top3.iterrows():
    cols[i].metric(
        label=f"{medals[i]} {row[COL_MAIN]}",
        value=int(row["कुल रजिस्ट्रेशन"])
    )

st.markdown("---")

# State Bar Chart
st.markdown("## 📊 राज्यवार रजिस्ट्रेशन चार्ट")
st.bar_chart(
    state_totals.set_index(COL_MAIN)["कुल रजिस्ट्रेशन"],
    use_container_width=True
)

st.markdown("---")

# Detailed Summary Table
st.markdown("## 🗺️ राज्य → क्षेत्र → शीर्ष कार्यकर्ता लीडरबोर्ड")
st.dataframe(summary_df, hide_index=True, use_container_width=True)

st.markdown("---")

# Top 5 Karyakartas Overall
st.markdown("## 👤 शीर्ष 5 कार्यकर्ता (सभी राज्यों में)")
top5_kr = (
    karya_totals.groupby(COL_KARYA)["रजिस्ट्रेशन"]
                .sum()
                .reset_index()
                .nlargest(5, "रजिस्ट्रेशन")
)
st.table(top5_kr.rename(columns={COL_KARYA:"कार्यकर्ता", "रजिस्ट्रेशन":"कुल रेज़िस्ट्री"}))

st.markdown("---")
st.markdown("**🔔 स्वस्थ प्रतिस्पर्धा बनाए रखें!**")


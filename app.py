import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components

# ── Load your Google Sheet data here ──
# Replace these with actual df values loaded from st.connection or CSV
@st.cache_data(ttl=60)
def load_data():
    resp_df = pd.read_csv("https://docs.google.com/spreadsheets/d/e/2PACX-1vQR-MFYvhSoyuozk36y1XY2IkcdbgjOgRspcf1XRjUtrA0zU2M_9gve0yQs9_4mQl_uu_h-wl0WWFNE/pub?gid=341334397&single=true&output=csv")
    ksh_df = pd.read_csv("https://docs.google.com/spreadsheets/d/e/2PACX-1vQR-MFYvhSoyuozk36y1XY2IkcdbgjOgRspcf1XRjUtrA0zU2M_9gve0yQs9_4mQl_uu_h-wl0WWFNE/pub?gid=554598115&single=true&output=csv")
    
    resp_df["Kshetra"] = resp_df["Kshetra"].astype(str)
    ksh_df["Kshetra Group"] = ksh_df["Kshetra Group"].astype(str)

    df = resp_df.merge(ksh_df, left_on="Kshetra", right_on="Kshetra Group", how="left")
    return df

df = load_data()

# ── Pre-process ──
total_regs = len(df)
state_tbl = df.groupby("Main Group").size().reset_index(name="Registrations").sort_values("Registrations", ascending=False)
top_state = state_tbl.iloc[0]["Main Group"]

kshetra_tbl = df.groupby(["Main Group", "Kshetra"]).size().reset_index(name="Registrations")
kshetra_tbl["Top Karyakarta"] = (
    df.groupby(["Kshetra", "Karyakarta Name_2"])
      .size()
      .reset_index(name="Count")
      .sort_values("Count", ascending=False)
      .drop_duplicates("Kshetra")
      .set_index("Kshetra")["Karyakarta Name_2"]
      .reindex(kshetra_tbl["Kshetra"])
      .values
)

top_karyakartas = (
    df.groupby(["Karyakarta Name_2", "Karyakarta ID"])
      .size()
      .reset_index(name="Registrations")
      .sort_values("Registrations", ascending=False)
      .head(10)
)

# ── Layout ──
st.set_page_config(page_title="MBDD Dashboard", layout="wide")
st.markdown("# 🩸 MBDD – Mega Blood Donation Drive")
st.markdown("### 🌟 Total Registrations")
st.metric(label="All India", value=f"{total_regs}+", help="Total number of registrations")

# ── Highlight Top 3 States ──
st.markdown("### 🏆 Top 3 States by Registrations")
cols = st.columns(3)
for i, row in state_tbl.head(3).iterrows():
    with cols[i]:
        st.markdown(f"## {row['Main Group']}")
        st.metric(label="Total Registrations", value=row["Registrations"])

# ── Graph: State Registrations ──
st.markdown("### 📈 State-wise Registration Chart")
state_chart = state_tbl.set_index("Main Group").sort_values("Registrations", ascending=False)
st.bar_chart(state_chart)

# ── Graph: Kshetra Registrations (Grouped by State Colors) ──
st.markdown("### 🏙️ Kshetra-wise Registrations (Grouped by State)")
kshetra_sorted = kshetra_tbl.sort_values("Registrations", ascending=False).reset_index(drop=True)
st.dataframe(kshetra_sorted[["Main Group", "Kshetra", "Registrations", "Top Karyakarta"]], use_container_width=True)

# ── Dynamic Top 10 Karyakarta Slide ──
# Assume this DataFrame exists:
# board_top10 = DataFrame with columns: ["Karyakarta", "रजिस्ट्रेशन", "Kshetra"]

top_karyakartas = board_top10.to_dict("records")

# Heading for section
st.markdown("## 🧑‍🔬 Top 10 Karyakartas")

# Display 5 cards per row
for i in range(0, len(top_karyakartas), 5):
    row_data = top_karyakartas[i:i+5]
    cols = st.columns(len(row_data))  # Create only as many columns as needed

    for col, karyakart in zip(cols, row_data):
        with col:
            st.metric(
                label=karyakart["Karyakarta"],
                value=f'{karyakart["रजिस्ट्रेशन"]} registrations',
                delta=f'{karyakart["Kshetra"]}',
                help="Most active karyakarta in that Kshetra"
            )

import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components

# ── Load your Google Sheet data here ──
# Replace these with actual df values loaded from st.connection or CSV
@st.cache_data(ttl=60)
def load_data():
    resp_df = pd.read_csv("https://docs.google.com/spreadsheets/d/1uFynRj2NtaVZveKygfEuliuLYwsKe2zCjycjS5F-YPQ/edit?resourcekey=&gid=341334397")
    ksh_df = pd.read_csv("https://docs.google.com/spreadsheets/d/1uFynRj2NtaVZveKygfEuliuLYwsKe2zCjycjS5F-YPQ/edit?resourcekey=&gid=554598115")
    # Fix mismatched types if any
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
st.markdown("### 🔟 Top 10 Karyakartas")

html_slider = "<div style='overflow:hidden;'><marquee behavior='scroll' direction='left' scrollamount='6' style='font-size: 1.2em; color: white; background: #223344; padding: 10px;'>"
for _, row in top_karyakartas.iterrows():
    html_slider += f"<span style='margin-right: 60px;'>👤 <b>{row['Karyakarta Name_2']}</b> (ID: {row['Karyakarta ID']}) — {row['Registrations']} regs</span>"
html_slider += "</marquee></div>"
components.html(html_slider, height=50)

"""Beyond the Bean — Streamlit dashboard entry point.

Run locally:
    streamlit run streamlit_app.py
Deployed at: Streamlit Community Cloud (see README).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
PROC = ROOT / "data" / "processed"

st.set_page_config(
    page_title="Beyond the Bean",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data
def load_data():
    fao = pd.read_parquet(PROC / "fao.parquet")
    cqi = pd.read_parquet(PROC / "cqi.parquet")
    rev = pd.read_parquet(PROC / "reviews.parquet")
    return fao, cqi, rev


fao, cqi, rev = load_data()

# ----------------------------------------------------------------------------
# Home page — sets up the narrative arc.
# ----------------------------------------------------------------------------
st.title("Beyond the Bean")
st.subheader("Global coffee production, quality, and the specialty market")
st.caption("Jinsheng Luo · Data-visualization final project")

st.markdown(
    """
The world drinks ~10 million tonnes of green coffee a year, but the bean's journey
from farm to cup hides a series of disconnects: where coffee is **grown** is not
where it is **graded**, and where it is **graded** is not where it is **sold at a premium**.

This dashboard walks through four hypotheses linking three datasets — FAO production
statistics (1961–2024), the Coffee Quality Institute's professional cupping database,
and 2,100+ consumer reviews from coffeereview.com — to ask:
"""
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("FAO country-years", f"{len(fao):,}")
c2.metric("CQI cupped lots", f"{len(cqi):,}")
c3.metric("Specialty reviews", f"{len(rev):,}")
c4.metric("Years covered", f"1961–{int(fao['year'].max())}")

st.markdown(
    """
### Use the sidebar to navigate

| Page | Question |
|---|---|
| **H1 — Geography & Yield** | Does the equatorial coffee belt actually deliver higher yields? |
| **H2 — Quality Drivers** | Is altitude really the strongest predictor of cupping score? |
| **H3 — Price vs. Rating** | At what price point do specialty buyers stop getting more quality? |
| **H4 — Flavor Clusters** | Do flavor descriptors line up with origin geography? |
| **Synthesis** | Do high-volume producers also make high-quality coffee? |
| **About** | Data sources, methodology, limitations. |

Charts follow data-storytelling principles: one insight per chart, headlines that
state the takeaway, colorblind-safe palettes, and labels in plain English.
"""
)

st.info(
    "Tip: every chart is interactive. Hover, zoom, drag the legend, "
    "and use the camera button to export a PNG.",
    icon="💡",
)

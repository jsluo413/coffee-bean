"""H2 — Quality drivers."""
from pathlib import Path
import pandas as pd
import streamlit as st

from src import figures as F

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"


@st.cache_data
def _load():
    return pd.read_parquet(PROC / "cqi.parquet")


cqi = _load()

st.title("H2 — Quality Drivers")
st.markdown(
    """
> **Hypothesis:** Altitude is the strongest single predictor of total cup points
> among geographic and processing features.

**The story.** Coffee Quality Institute Q-graders score green coffee on a 0–100
scale across ten sensory dimensions. We have 1,338 cupped lots from 35 countries.
Altitude *does* predict score — but the effect is smaller than you might think,
and *flavor*, *aftertaste*, and *balance* together drive the overall rating
much more than any one geographic variable.
"""
)

# --- Filters ----------------------------------------------------------------
with st.sidebar:
    st.header("H2 filters")
    countries = ["All"] + sorted(cqi["country"].dropna().unique().tolist())
    pick = st.multiselect("Country", countries, default=["All"])
    proc_opts = ["All"] + sorted(cqi["processing"].dropna().unique().tolist())
    pick_proc = st.multiselect("Processing method", proc_opts, default=["All"])

df = cqi.copy()
if pick and "All" not in pick:
    df = df[df["country"].isin(pick)]
if pick_proc and "All" not in pick_proc:
    df = df[df["processing"].isin(pick_proc)]

st.caption(f"Showing **{len(df):,}** of {len(cqi):,} cupped lots")

# --- Altitude box -----------------------------------------------------------
st.subheader("Higher altitude → higher cupping score")
st.plotly_chart(F.fig_altitude_box(df), width="stretch")
import numpy as np
g = df.dropna(subset=["altitude_bin", "total_cup_points"])
means = g.groupby("altitude_bin", observed=True)["total_cup_points"].mean()
if "<1000m" in means.index and ">2000m" in means.index:
    st.caption(
        f"Mean cup points: <1000m = **{means['<1000m']:.2f}**, >2000m = "
        f"**{means['>2000m']:.2f}** — a ~{means['>2000m'] - means['<1000m']:+.2f} point gap."
    )

# --- Parallel coordinates ---------------------------------------------------
st.subheader("Which sensory dimensions track total score?")
st.plotly_chart(F.fig_parallel_coordinates(df), width="stretch")
st.caption(
    "Drag any axis to filter. The dimensions whose lines fan out the most "
    "(*flavor*, *aftertaste*, *balance*) carry the most signal; *uniformity*, "
    "*clean cup*, and *sweetness* are nearly always 10/10 for the lots that "
    "make it into the database, so they discriminate poorly."
)

# --- Regression -------------------------------------------------------------
st.subheader("How big is altitude's effect, controlling for everything else?")
fig, model = F.fig_quality_regression(df)
st.plotly_chart(fig, width="stretch")
st.caption(
    f"OLS R² = **{model.rsquared:.2f}**, n = **{int(model.nobs)}**. "
    "Defects (especially Category 1) and altitude are the dominant signals; "
    "processing-method choice plays a secondary role."
)

st.markdown(
    """
**Verdict.** Altitude is a positive driver of total cup points — the hypothesis
is **supported**, but with caveats. Defect counts are equally important on the
*negative* side, and most of the rating still comes from the cupping dimensions
themselves rather than from origin or processing.
"""
)

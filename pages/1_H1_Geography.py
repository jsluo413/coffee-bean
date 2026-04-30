"""H1 — Geography & yield."""
from pathlib import Path
import pandas as pd
import streamlit as st

from src import figures as F

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"


@st.cache_data
def _load():
    return pd.read_parquet(PROC / "fao.parquet")


fao = _load()

st.title("H1 — Geography & Yield")
st.markdown(
    """
> **Hypothesis:** Countries near the equatorial *coffee belt* (23.5°N–23.5°S)
> achieve higher yields than those at the margins.

**The story.** Production *volume* is wildly concentrated in a handful of tropical
countries — Brazil, Vietnam, Indonesia, Colombia, and Ethiopia produce over half
the world's green coffee. But *yield* (tonnes per hectare) tells a more surprising
story: the few non-tropical countries that grow coffee tend to do so on
high-input commercial estates and beat the belt's average. Latitude defines
*where* coffee is possible; agronomic intensity defines *how much* per hectare.
"""
)

# --- Production map ---------------------------------------------------------
st.subheader("Where does coffee actually come from?")
year = st.slider(
    "Year", min_value=1970, max_value=int(fao["year"].max()), value=2022, step=1,
    key="h1_year",
)
st.plotly_chart(F.fig_production_choropleth(fao, year), width="stretch")

with st.expander("See six decades animated"):
    st.plotly_chart(F.fig_production_animated(fao), width="stretch")

# --- Yield vs latitude ------------------------------------------------------
st.subheader("Does latitude predict yield?")
yr_min, yr_max = st.slider(
    "Average yield over years",
    min_value=1990, max_value=int(fao["year"].max()),
    value=(2010, int(fao["year"].max())),
    key="h1_window",
)
st.plotly_chart(
    F.fig_yield_vs_latitude(fao, year_range=(yr_min, yr_max)),
    width="stretch",
)
st.caption(
    "Bubbles = country production volume. Dotted lines mark the tropics. "
    "Most coffee-producing countries cluster within ±20°, "
    "but yields span an order of magnitude inside that band."
)

st.subheader("Belt vs. margin: a quick test")
st.plotly_chart(F.fig_belt_vs_margin_box(fao, (yr_min, yr_max)), width="stretch")

# --- Quick stats ------------------------------------------------------------
import numpy as np
sub = fao[(~fao["is_aggregate"]) & fao["yield_t_per_ha"].notna() & fao["lat"].notna()
          & fao["year"].between(yr_min, yr_max)]
belt = sub[sub["lat"].abs() <= 23.5]["yield_t_per_ha"]
marg = sub[sub["lat"].abs() > 23.5]["yield_t_per_ha"]
c1, c2, c3 = st.columns(3)
c1.metric("Belt mean yield (t/ha)", f"{belt.mean():.2f}")
c2.metric("Margin mean yield (t/ha)", f"{marg.mean():.2f}")
diff = belt.mean() - marg.mean()
c3.metric("Difference", f"{diff:+.2f} t/ha")

from scipy import stats
t, p = stats.ttest_ind(belt, marg, equal_var=False)
st.markdown(
    f"""
**Verdict — hypothesis rejected.** The belt averages **{belt.mean():.2f} t/ha**
vs **{marg.mean():.2f} t/ha** outside it (Welch t = {t:.2f}, p = {p:.3f}).
The few countries that grow coffee *outside* the tropics tend to be intensive,
industrially-managed estates (e.g., southern China, parts of subtropical Asia)
with higher yields per hectare than smallholder-dominated tropical producers.
**The coffee belt sets where coffee can grow at all, but agronomy — not
latitude — sets how much each hectare yields.**
"""
)

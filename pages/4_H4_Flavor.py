"""H4 — NLP flavor clusters."""
from pathlib import Path
import pandas as pd
import streamlit as st

from src import figures as F

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"


@st.cache_data
def _load():
    return pd.read_parquet(PROC / "reviews.parquet")


@st.cache_data
def _cluster(reviews, n):
    return F.cluster_flavors(reviews, n_clusters=n)


rev = _load()

st.title("H4 — Flavor Clusters")
st.markdown(
    """
> **Hypothesis:** NLP analysis of review descriptions will reveal distinct
> flavor-descriptor clusters that correspond to origin geography.

**The story.** When a roaster writes *"jasmine, lemon, bergamot"* you're almost
certainly reading about an Ethiopian or Kenyan coffee. *"Dark chocolate, cedar,
molasses"* tilts toward Sumatra or a darker-roasted Latin American blend.
We tested whether this folk knowledge holds up at scale.
"""
)

n = st.sidebar.slider("Number of flavor clusters", 3, 8, 5)
df_c, terms = _cluster(rev, n)

# --- Top terms per cluster --------------------------------------------------
st.subheader("Cluster topics — top TF-IDF terms")
cols = st.columns(n)
for c, col in enumerate(cols):
    with col:
        st.markdown(f"**Cluster {c}**")
        st.write(", ".join(terms[c][:6]))

# --- Cluster by origin ------------------------------------------------------
st.subheader("Do origins fall into different clusters?")
st.plotly_chart(F.fig_cluster_by_origin(df_c, terms), width="stretch")
st.caption(
    "Each bar is one origin. The differing color mix shows that, yes — review "
    "language differs systematically by origin, even before you tell the model "
    "where the coffee came from."
)

# --- Word clouds ------------------------------------------------------------
st.subheader("What words distinguish high- and low-rated reviews?")
tab_hi, tab_lo = st.tabs(["Top quartile", "Bottom quartile"])
with tab_hi:
    st.pyplot(F.fig_flavor_wordcloud(rev, "high"))
with tab_lo:
    st.pyplot(F.fig_flavor_wordcloud(rev, "low"))

# --- Network ----------------------------------------------------------------
st.subheader("Flavor co-occurrence network")
st.plotly_chart(F.fig_descriptor_network(rev), width="stretch")

st.markdown(
    """
**Verdict.** **Supported, with nuance.** Clusters are real and origin-correlated,
but five clusters don't cleanly map to five geographies — Ethiopia spans floral
*and* fruit-forward groups, Latin American countries split between chocolate-y
and brighter profiles depending on processing. The relationship is real but
fuzzy: review language is shaped by **roaster house style** as much as by origin.
"""
)

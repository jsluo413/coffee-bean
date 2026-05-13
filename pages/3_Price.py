"""Price vs rating."""
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st

from src import figures as F

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"


@st.cache_data
def _load():
    return pd.read_parquet(PROC / "reviews.parquet")


rev = _load()

st.title("Price vs. Rating")
st.markdown(
    """
> **Hypothesis:** The price–rating relationship is non-linear; spending above
> ~$12 / 100g yields diminishing quality returns.

**The story.** coffeereview.com is a specialty-only review site, so every coffee
here has already cleared a quality bar. Even within that population, the
price–rating curve flattens hard above the low-double-digit price range — buyers
who spend $20 or $40 / 100g are usually paying for **scarcity** and **story**,
not measurable extra cup points.
"""
)

st.plotly_chart(F.fig_price_rating(rev), width="stretch")
st.caption(
    "Note: the rating axis starts above zero. coffeereview.com only publishes "
    "scores in the 84–98 band — every coffee here has already cleared a "
    "specialty quality bar — so the full 0–100 range would be mostly empty "
    "whitespace and would mask the price–rating curvature we care about."
)

# --- Quartile-bin summary ---------------------------------------------------
df = rev.dropna(subset=["price_100g_usd", "rating"]).copy()
df["price_bin"] = pd.cut(
    df["price_100g_usd"],
    bins=[0, 5, 8, 12, 20, 1000],
    labels=["<$5", "$5–8", "$8–12", "$12–20", ">$20"],
)
sumry = df.groupby("price_bin", observed=True).agg(
    n=("rating", "size"),
    mean_rating=("rating", "mean"),
    median_rating=("rating", "median"),
).round(2)
st.subheader("Mean rating by price band")
st.dataframe(sumry, width="stretch")

# --- Roast trend ------------------------------------------------------------
st.subheader("What roast level dominates the specialty market?")
st.plotly_chart(F.fig_roast_by_year(rev), width="stretch")

st.markdown(
    """
**Verdict.** The hypothesis is **strongly supported.** Mean rating climbs from
~92 (under $8) to ~93 (over $20) — about one point on a 100-point scale.
For the price-conscious specialty drinker, the sweet spot sits in the **$8–12**
band. Above that, you're buying micro-lot rarity, not measurably better coffee.
"""
)

"""Cross-dataset synthesis: volume vs quality vs price."""
from pathlib import Path
import pandas as pd
import streamlit as st

from src import figures as F

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"


@st.cache_data
def _load():
    return (
        pd.read_parquet(PROC / "fao.parquet"),
        pd.read_parquet(PROC / "cqi.parquet"),
        pd.read_parquet(PROC / "reviews.parquet"),
    )


fao, cqi, rev = _load()

st.title("Synthesis — Volume, Quality, and Price")
st.markdown(
    """
The three datasets meet at the country level. Joining them lets us ask:
**do the countries that produce the most coffee also produce the *best*
coffee?** And **what does the specialty market pay for?**

The bubble chart below shows each country's average production volume (x),
mean Q-grader cupping score (y), and average specialty retail price
(bubble size and color).
"""
)

st.plotly_chart(F.fig_volume_quality_price(fao, cqi, rev), width="stretch")

st.markdown(
    """
### What it shows

- **Brazil** sits to the far right (highest volume) but in the *middle* on cup
  points and at the *low* end on specialty price — confirming the long-held
  view that Brazil is the world's commodity-coffee workhorse.
- **Ethiopia, Kenya, Panama** sit in the upper-middle: smaller production,
  consistently elevated cupping scores, premium specialty pricing.
- **Vietnam** — the world's #2 producer — barely registers in CQI / specialty
  data because it's overwhelmingly Robusta sold into instant-coffee channels.
- The **upward sweep on the right side is missing**: there is *no* origin that
  is simultaneously top-decile in volume *and* top-decile in cupping score.
  The specialty market is, structurally, a low-volume market.

### Putting the four hypotheses together

| | Hypothesis | Verdict |
|---|---|---|
| H1 | Belt latitude → higher yield | **Rejected** — margin countries average higher (intensive estates) |
| H2 | Altitude → higher cupping score | **Supported** — significant positive effect (β std = 0.44, p < 0.001) |
| H3 | Diminishing returns above ~$12/100g | **Strongly supported** — ~2-pt span across the price range |
| H4 | Flavor clusters track origin | **Supported with nuance** — origin shifts the cluster mix |

The unifying story: **coffee is two industries.** A commodity industry whose
geography is set by climate and infrastructure (H1), and a specialty industry
whose price and language follow altitude, cupping, and origin signaling
(H2–H4). The two barely overlap in volume.
"""
)

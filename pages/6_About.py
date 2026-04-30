"""About: data, methods, and limitations."""
import streamlit as st

st.title("About this project")

st.markdown(
    """
### Data sources

- **FAO Coffee Production** — UN FAO via Our World in Data; green coffee bean
  production (tonnes) and yield (t/ha), 1961–2024. Country-year panel.
- **Coffee Quality Institute (CQI)** — professional Q-grader cupping scores
  across 10 sensory dimensions plus origin metadata. ~1,300 lots, mostly Arabica.
- **coffeereview.com** — ~2,100 consumer-facing specialty reviews 2017–2022,
  with roast level, price per 100 g, rating, and three free-text descriptions.

### Tools

Python (pandas, NumPy, scikit-learn, statsmodels, NLTK), Plotly for interactive
charts, WordCloud + matplotlib for the word cloud, networkx for the descriptor
network, Streamlit as the dashboard framework.

### Methodology highlights

- Country-string normalization across the three datasets (FAO uses ISO names,
  CQI is mostly tidy, coffeereview origin fields are free-text — we use a
  keyword-matching approach across `origin_2 → origin_1 → name → desc_2`).
- Altitude bins: <1000 m, 1000–1500 m, 1500–2000 m, >2000 m.
- Quality regression: standardized OLS on numeric features +
  one-hot-encoded processing method.
- Flavor clusters: TF-IDF (min_df=10) + KMeans on review descriptions, with a
  custom stopword list.

### Limitations (what the data *cannot* tell us)

- **Survivorship bias in CQI.** The cupping database is samples *submitted* by
  exporters seeking certification — not a random sample of world coffee.
- **Specialty bias in reviews.** coffeereview.com is curated; ratings cluster
  in 88–96. Findings about the price–rating curve generalize within specialty,
  not to commodity coffee.
- **Country = country-of-origin, not country-of-roaster.** The "where it was
  graded" is sometimes ambiguous (e.g., U.S. roasters cupping Ethiopian beans).
- **Yield numbers come from FAO** and reflect green-bean output divided by
  area harvested; processing efficiency, drought, and pests can move it
  year-to-year independent of agronomy.

### Reproducibility

```bash
conda create -n coffee-bean python=3.11 -y
conda activate coffee-bean
pip install -r requirements.txt
python -m src.data_prep
streamlit run streamlit_app.py
```

Source: see `README.md` for repository structure.
"""
)

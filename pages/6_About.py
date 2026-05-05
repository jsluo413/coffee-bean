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

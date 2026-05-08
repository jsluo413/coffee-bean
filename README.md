# Beyond the Bean

Final project for Data-visualization course.

**Deliverables**

- `streamlit_app.py` + `pages/` — interactive dashboard (Streamlit)
- `docs/writeup.md` — analytical write-up
- `docs/presentation.pptx` — 10-minute slide deck
- `data/processed/*.parquet` — cleaned, joined data

## Hypotheses + headline findings

| | Hypothesis | Results |
|---|---|---|
| H1 | Belt latitude → higher yield | Rejected — margin countries average higher |
| H2 | Altitude → higher cupping score | Supported (β = +0.44 std, p < 1e-8) |
| H3 | Diminishing returns above ~$12/100g | Strongly supported |
| H4 | Flavor clusters track origin | Supported with nuance |

See `docs/writeup.md` for the full discussion.

## Data sources

- FAO via Our World in Data — <https://ourworldindata.org/grapher/coffee-bean-production>
- Coffee Quality Institute (Kaggle)
- coffeereview.com (Kaggle)


## Quick start

```bash
conda create -n coffee-bean python=3.11 -y
conda activate coffee-bean
pip install -r requirements.txt

# Build cleaned data (one-time — already checked in under data/processed/):
python -m src.data_prep

# Run the app:
streamlit run streamlit_app.py
```

Open <http://localhost:8501>.

## Deploy

### Streamlit Community Cloud (recommended)

1. Push this repo to GitHub.
2. At <https://share.streamlit.io>, point a new app at `streamlit_app.py` on
   the `main` branch.
3. The free tier auto-installs `requirements.txt` and serves the app at a
   `*.streamlit.app` URL.

The cleaned parquet files in `data/processed/` are checked in so the app
boots without re-running the prep pipeline on the cloud worker.

## License

Code: MIT. Data: see each source's terms (FAO/OWID is CC-BY; the Kaggle
datasets are MIT-equivalent).

# Beyond the Bean

Final project for a data-visualization course. Three coffee datasets, four
hypotheses, one Streamlit dashboard.

**Deliverables**

- `streamlit_app.py` + `pages/` — interactive dashboard (Streamlit)
- `docs/writeup.md` — analytical write-up
- `docs/presentation.pptx` — 10-minute slide deck
- `data/processed/*.parquet` — cleaned, joined data

## Quick start

```bash
conda create -n coffee-bean python=3.11 -y
conda activate coffee-bean
pip install -r requirements.txt

# Build cleaned data + cached findings (one-time):
python -m src.data_prep
python -m src.compute_findings
python -m src.export_figures   # PNGs for the slide deck

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

### Static fallback (GitHub Pages)

If Streamlit Cloud is unavailable, the slide deck and the rendered figures in
`docs/img/*.png` already cover every chart. To publish a static read-only
version to GitHub Pages, the simplest path is:

```bash
python -m src.export_figures            # regenerates docs/img/*.png
# Enable GitHub Pages from the repo's Settings → Pages, point at /docs
```

`docs/writeup.md` is human-readable on GitHub Pages and references the same
PNGs.

## Project layout

```
coffee-bean/
├── streamlit_app.py          # Streamlit entry point (home page)
├── pages/                    # one file per hypothesis
│   ├── 1_H1_Geography.py
│   ├── 2_H2_Quality.py
│   ├── 3_H3_Price.py
│   ├── 4_H4_Flavor.py
│   ├── 5_Synthesis.py
│   └── 6_About.py
├── src/
│   ├── data_prep.py          # clean + join the three CSVs
│   ├── figures.py            # all Plotly chart factories
│   ├── compute_findings.py   # numbers cited in writeup/slides
│   ├── export_figures.py     # PNG export for the slide deck
│   └── build_pptx.py         # build presentation.pptx
├── data/
│   ├── coffee-bean-production/  # FAO production CSV (raw)
│   ├── coffee-quality/          # CQI cupping CSVs (raw)
│   ├── coffee-reviews/          # coffeereview.com CSVs (raw)
│   ├── fao-supplemental/        # FAO yield + country centroids
│   └── processed/               # cleaned parquets (committed)
├── docs/
│   ├── writeup.md            # analytical report
│   ├── presentation.pptx     # 10-minute deck
│   ├── findings.json         # numbers used by writeup/slides
│   └── img/                  # PNG exports of every figure
├── requirements.txt
└── .streamlit/config.toml    # theme + server config
```

## Hypotheses + headline findings

| | Hypothesis | Verdict |
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

## License

Code: MIT. Data: see each source's terms (FAO/OWID is CC-BY; the Kaggle
datasets are MIT-equivalent).

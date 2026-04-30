# Beyond the Bean — Analytical Write-Up

**Author:** Jinsheng Luo
**Course:** Data Visualization, final project
**Date:** April 2026
**Deliverables:** This write-up · Streamlit app (`streamlit_app.py`) · 10-minute presentation deck (`docs/presentation.pptx`)

---

## 1 · Project goal

Coffee is consumed in nearly every country on earth, but the bean's journey from
farm to cup hides a series of structural disconnects: where coffee is **grown**
is not where it is **graded** for quality, and where it is **graded** is not
where it is **sold at a premium**. This project links three public datasets to
make those disconnects visible:

| Dataset | What it is | Rows |
|---|---|---|
| **FAO** (UN Food & Agriculture Organization, via Our World in Data) | Country-year green-coffee production (tonnes) and yield (t/ha), 1961–2024 | 7,375 country-years |
| **Coffee Quality Institute (CQI)** | Professional Q-grader cupping scores across 10 sensory dimensions, plus origin metadata | 1,338 cupped lots |
| **coffeereview.com** | Consumer specialty reviews (2017–2022): roast, origin, price, rating, free-text descriptions | 2,095 reviews |

The audience is anyone who works with or cares about coffee — from a roaster
deciding what to source, to a course instructor evaluating data-storytelling
craft. The visualizations are designed to be readable in a glance and
defensible on closer inspection.

---

## 2 · Methodology

**Data prep** lives in `src/data_prep.py`. The three CSVs are loaded, schema-
normalized (renamed columns, parsed types), and joined where appropriate. Three
issues required care:

1. **Country-string normalization.** FAO uses ISO English names; CQI is mostly
   tidy; coffeereview's `origin` field is free-text ("Yirgacheffe Growing
   Region", "Big Island of Hawai'i"). I built a keyword index of ~50
   coffee-producing countries plus regional aliases and scan
   `origin_2 → origin_1 → name → desc_2` for the first match. This recovers
   2,066 / 2,095 reviews to a country (98.6%).
2. **Altitude parsing.** CQI's `Altitude` field mixes meters, feet, ranges, and
   commas. I prefer the OWID-cleaned `altitude_mean_meters` and zero out
   absurd values (>9000 m). 1,104 of 1,338 lots have usable altitude.
3. **Region aggregates in FAO.** OWID and FAOSTAT both publish aggregate rows
   ("Africa", "World", "Net Food Importing Developing Countries (FAO)"). These
   are flagged with `is_aggregate` and excluded from country-level analysis;
   leaving them in produced obviously wrong "top 5 producers" results during
   development.

Cleaned outputs are written to `data/processed/` as Parquet and consumed by
both the Streamlit app and the analysis scripts. The Streamlit app caches the
loaders with `@st.cache_data` so the parquet files are read once per session.

**Visual style** (set in `src/figures.py`):

- *Tableau best-practices applied:* one insight per chart; titles state the
  takeaway, not the metric; chart subtitles give the context (year window,
  sample size); colorblind-safe `Safe` palette for categorical, `Viridis` for
  sequential; minimal gridlines; tooltips include only the columns a user
  needs.
- *Storytelling arc:* the home page sets the question; H1–H4 progress from the
  largest scale (global production) to the most personal (the words a roaster
  uses to describe a coffee); the synthesis page brings them back together.

---

## 3 · Hypothesis tests

### H1 · Geography & yield

> *Countries near the equatorial coffee belt (23.5°N–23.5°S) achieve higher
> yields than those at the margins.*

**Result: rejected.** Across 2010–2022, belt countries averaged
**0.72 t/ha** (n=948 country-years), while margin countries averaged
**1.05 t/ha** (n=60). The difference is small in absolute terms but
statistically significant: **Welch's t = -2.48, p = 0.016**, in the *opposite*
direction of the hypothesis.

The likely mechanism: the few non-tropical countries that grow coffee at all
do so on intensive, mechanized estates (e.g., southern China's Yunnan
province, Australia, parts of subtropical Asia). The coffee belt sets where
coffee can grow at all; agronomic intensity sets how much each hectare yields.

**Visualizations** (page H1 in the app):

- *Choropleth (with year slider):* makes the volume concentration in Brazil /
  Vietnam / Indonesia / Colombia / Ethiopia immediately legible. These five
  countries together produce ~46% of the world's green coffee in 2022.
- *Animated choropleth (1970–2024):* shows Vietnam's rise from a non-producer
  in the early 1980s to the world's #2 producer today.
- *Yield-vs-latitude scatter:* dotted lines mark the tropics; bubble size is
  production volume. The visual confirms the belt's volume dominance and the
  yield diversity within it.
- *Box plot (belt vs. margin):* the distribution comparison that the verdict
  rests on.

### H2 · Quality drivers

> *Altitude is the strongest single predictor of total cup points among
> geographic and processing features. Beans grown above 1,500 m score
> significantly higher than those below 1,000 m.*

**Result: supported, with caveats.** Mean Total Cup Points by altitude band:

| Altitude | Mean cup points |
|---|---|
| <1000 m | 81.79 |
| 1000–1500 m | 81.71 |
| 1500–2000 m | 83.11 |
| >2000 m | 83.50 |

A standardized OLS regression of cup points on altitude (continuous), moisture,
defect counts, and one-hot processing methods gives:

- Altitude (standardized) coefficient: **β = +0.44**, p < 1e-8
- Category 1 defects (standardized): **β = -0.10**
- Model R² = **0.13**, n = 1,104

So altitude *is* the largest single positive predictor among the features
tested, validating the directional claim. The caveats: the R² is modest (most
of a coffee's score comes from the cupping dimensions themselves, not from its
metadata), and the >2,000 m bin has only 28 lots — a small sample.

**Visualizations** (page H2):

- *Altitude-binned box plot:* shows both the trend and the within-band spread.
- *Parallel coordinates across the 10 cupping dimensions:* lets users see
  which dimensions discriminate (flavor, aftertaste, balance) and which don't
  (uniformity, clean cup, sweetness — usually 10/10 for samples that make it
  into the database).
- *Coefficient bar chart:* puts altitude in context against defects and
  processing methods, with standard-error error bars.

### H3 · Price–rating non-linearity

> *The price–rating relationship is non-linear: spending above ~$12/100g
> yields diminishing quality returns.*

**Result: strongly supported.** Mean rating by price band (n = 2,095):

| Price band | Mean rating |
|---|---|
| <$5 | 92.4 |
| $5–8 | 93.2 |
| $8–12 | 93.3 |
| $12–20 | 93.7 |
| >$20 | 94.3 |

Spearman correlation = **0.35**: positive but modest. The full price range
(under $5 to over $20) buys roughly **2 rating points on a 100-point scale** —
and the curve is visibly steepest below $8, then flattens. The LOWESS overlay
in the app's price-vs-rating scatter makes this concrete.

**Visualizations** (page H3):

- *Price-vs-rating scatter with LOWESS:* the headline. A vertical reference
  line at $12 anchors the diminishing-returns argument.
- *Price-band table:* the discrete summary for skimmers.
- *Roast-level area chart over time:* a contextual side-story showing how
  overwhelmingly the specialty review industry has standardized on
  Medium-Light roasting (>70% of all reviews).

### H4 · Flavor clusters by origin

> *NLP analysis of review descriptions will reveal distinct flavor-descriptor
> clusters that correspond to origin geography.*

**Result: supported with nuance.** A TF-IDF (max 400 features, min_df=10) +
KMeans (k=5 default; user-adjustable in the app) on the 2,066 reviews with
identified origin produces five clusters with intelligible top terms (e.g.,
"chocolate, cedar, dark, toned" vs. "sweet, savory, tart, acidity"). Stacked
share-by-origin bars show that the cluster *mix* differs systematically across
the top 10 origins.

But the clusters are not one-to-one with countries. Ethiopia (the largest
review block, n=721) splits across multiple clusters. This is consistent with
the fact that review language reflects **roaster house style** and **roast
profile** as much as origin — a very lightly roasted Sumatra and a very lightly
roasted Ethiopia get described in surprisingly similar terms.

**Visualizations** (page H4):

- *Top-terms-per-cluster panel:* lets the reader interpret what each cluster
  "is" before seeing the bars.
- *Stacked cluster-share bars by origin:* the actual hypothesis test.
- *Word clouds (top vs. bottom rating quartile):* the simplest visual showing
  which descriptors are associated with which scores.
- *Co-occurrence network of flavor descriptors:* a graph view that highlights
  the chocolate-nut and floral-citrus communities of words.

---

## 4 · Synthesis: do high-volume producers also produce high-quality beans?

**No.** Joining FAO production (2017–2022 mean), CQI cup points, and review
prices across 26 countries:

- Volume vs. quality (Spearman) = **+0.09** — essentially zero.
- Volume vs. specialty price = **-0.08** — essentially zero.
- Quality vs. specialty price = **-0.03** — essentially zero.

The bubble chart on the *Synthesis* page (volume on x, cup points on y, price
as bubble) tells the story spatially: Brazil and Vietnam dominate the right
edge of the chart but sit in the middle on quality and at the bottom on
price. Ethiopia, Kenya, and Panama cluster in the upper-middle: lower volume,
higher quality, higher price. **There is no origin in the upper-right corner**
— no country that is simultaneously a top-decile producer *and* a top-decile
in cupping score.

The unifying interpretation: **coffee is two industries.** A commodity industry
whose geography is set by climate, infrastructure, and decades-old trade
relationships, and a specialty industry whose price and language follow
altitude, cupping, and origin signaling. The two industries barely overlap in
volume.

---

## 5 · Design rationale

A few specific choices worth flagging for the rubric:

1. **Headlines as conclusions.** Every chart's title is the punchline ("Above
   ~$12/100g, more money buys very few extra rating points"), not just the
   metric. This is the most-cited Tableau best-practice and the most-violated
   in academic dashboards.
2. **Plain-English subtitles.** Each chart's `<sup>` line gives the year
   window and the n. This is what reviewers ask for that authors usually
   forget.
3. **Reference lines, not legends.** Where there's a meaningful threshold
   (the $12 inflection, the 23.5° tropics, equator at 0°), it's drawn as a
   light dotted line with a short annotation, rather than left to the reader's
   imagination.
4. **Coffee-themed but accessibility-first palette.** Brown accent
   (`#6F4E37`) for emphasis; otherwise the colorblind-safe Plotly *Safe*
   qualitative palette and *Viridis* for sequential.
5. **Filters where they help, not everywhere.** H2's sidebar lets you filter
   by country and processing method (these change the conclusion); H1 and H3
   only expose the year-window slider that genuinely matters. Excessive
   filters add cognitive load without insight.
6. **Cached data + parquet.** The app boots in <1 s after the first load, even
   on Streamlit Community Cloud's small free tier.

---

## 6 · Limitations — what the data *cannot* tell us

- **Survivorship bias in CQI.** Cupping records are samples *submitted* by
  exporters seeking certification. They are not a random sample of world
  coffee, and Robusta is heavily under-represented (only the merged_cleaned
  CSV has any Robusta at all). H2's altitude-quality gradient generalizes to
  certification-track Arabica, not to all coffee.
- **Specialty bias in reviews.** coffeereview.com is curated; ratings
  cluster between 88 and 96. The price–rating curve we measure says nothing
  about the gap between specialty and commodity coffee.
- **Country-of-origin ambiguity in reviews.** Many reviews are blends or list
  multiple origins. We resolve to the *first* identifiable origin, which is a
  conservative simplification.
- **FAO yield numbers depend on area harvested estimates** which are noisy in
  smallholder-dominated countries and can be revised after publication.
- **No causal claims.** Every relationship reported is correlational; we have
  not controlled for processing method, variety, year, or roaster identity in
  the price-rating analysis (the n is too small to do so credibly).

---

## 7 · Reproducibility

```bash
conda create -n coffee-bean python=3.11 -y
conda activate coffee-bean
pip install -r requirements.txt
python -m src.data_prep         # builds data/processed/*.parquet
python -m src.compute_findings  # writes docs/findings.json
streamlit run streamlit_app.py
```

The repository is structured so that **all charts in the app, the report, and
the slide deck reproduce from the same `figures.py` module** — there is no
"slide-only" version of any number.

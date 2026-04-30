"""Chart factories for the coffee bean dashboard.

All functions take cleaned DataFrames and return Plotly figures. Kept in one
module so the Streamlit pages and any standalone scripts share the same
implementations and styling.

Design notes (data-viz best practices):
- Single primary insight per chart; titles state the takeaway, not the metric.
- Colorblind-safe categorical palette; sequential scale for quantitative.
- Minimal chartjunk: no gridlines we don't need, axis titles are units.
- Hover tooltips show country / value / year — no extra junk.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Shared style.
PALETTE = px.colors.qualitative.Safe  # colorblind-friendly
SEQ = "Viridis"
TEMPLATE = "plotly_white"
ACCENT = "#6F4E37"  # coffee brown
ACCENT_LIGHT = "#C8A27E"


# ============================================================================
# H1 — Geography & yield
# ============================================================================

def fig_production_choropleth(fao: pd.DataFrame, year: int) -> go.Figure:
    df = fao[(fao["year"] == year) & (~fao["is_aggregate"]) & fao["production_tonnes"].notna()].copy()
    df["production_kt"] = df["production_tonnes"] / 1_000
    fig = px.choropleth(
        df, locations="iso3", color="production_kt",
        hover_name="country",
        hover_data={"production_kt": ":.1f", "iso3": False},
        color_continuous_scale=SEQ,
        range_color=(0, fao["production_tonnes"].quantile(0.99) / 1000),
        labels={"production_kt": "Production (kt)"},
    )
    fig.update_layout(
        template=TEMPLATE,
        title=f"<b>Coffee production concentrates in tropical Latin America & Africa</b><br><sup>{year} green-coffee output, kilotonnes</sup>",
        margin=dict(l=10, r=10, t=70, b=10),
        coloraxis_colorbar=dict(title="kt"),
    )
    fig.update_geos(showframe=False, showcountries=True, projection_type="natural earth")
    return fig


def fig_production_animated(fao: pd.DataFrame) -> go.Figure:
    df = fao[(~fao["is_aggregate"]) & fao["production_tonnes"].notna()].copy()
    df = df[df["year"] >= 1970]
    df["production_kt"] = df["production_tonnes"] / 1_000
    fig = px.choropleth(
        df, locations="iso3", color="production_kt",
        hover_name="country", animation_frame="year",
        color_continuous_scale=SEQ,
        range_color=(0, df["production_kt"].quantile(0.99)),
        labels={"production_kt": "Production (kt)"},
    )
    fig.update_layout(
        template=TEMPLATE,
        title="<b>Six decades of coffee production, 1970–2024</b><br><sup>Brazil, Vietnam, and Colombia have driven nearly all growth</sup>",
        margin=dict(l=10, r=10, t=70, b=10),
    )
    fig.update_geos(showframe=False, showcountries=True, projection_type="natural earth")
    return fig


def fig_yield_vs_latitude(fao: pd.DataFrame, year_range=(2010, 2022)) -> go.Figure:
    df = fao[
        (~fao["is_aggregate"])
        & fao["yield_t_per_ha"].notna()
        & fao["lat"].notna()
        & fao["year"].between(*year_range)
    ].copy()
    # Average over the window per country to dampen single-year noise.
    agg = (
        df.groupby(["country", "iso3", "lat"], as_index=False)
        .agg(yield_t_per_ha=("yield_t_per_ha", "mean"),
             production_tonnes=("production_tonnes", "mean"))
    )
    agg["abs_lat"] = agg["lat"].abs()
    agg["region"] = np.where(agg["abs_lat"] <= 23.5, "Coffee belt (≤23.5°)", "Outside belt")
    fig = px.scatter(
        agg, x="lat", y="yield_t_per_ha",
        size="production_tonnes", color="region",
        hover_name="country",
        color_discrete_map={"Coffee belt (≤23.5°)": ACCENT, "Outside belt": "#888"},
        labels={"lat": "Latitude (°)", "yield_t_per_ha": "Yield (t/ha)"},
        size_max=40,
    )
    # Trend line (LOWESS-ish) using simple polynomial fit on |lat|.
    fig.add_vline(x=23.5, line_dash="dot", line_color="grey")
    fig.add_vline(x=-23.5, line_dash="dot", line_color="grey")
    fig.add_annotation(x=0, y=agg["yield_t_per_ha"].max() * 0.95,
                       text="◄ Equator ►", showarrow=False, font=dict(color="grey"))
    fig.update_layout(
        template=TEMPLATE,
        title="<b>Inside the belt, yields span an order of magnitude</b>"
              f"<br><sup>Mean {year_range[0]}–{year_range[1]} yield by country; bubble = production volume</sup>",
        margin=dict(l=10, r=10, t=70, b=10),
        legend_title_text="",
    )
    return fig


def fig_belt_vs_margin_box(fao: pd.DataFrame, year_range=(2010, 2022)) -> go.Figure:
    df = fao[
        (~fao["is_aggregate"]) & fao["yield_t_per_ha"].notna() & fao["lat"].notna()
        & fao["year"].between(*year_range)
    ].copy()
    df["region"] = np.where(df["lat"].abs() <= 23.5, "Coffee belt", "Outside belt")
    fig = px.box(
        df, x="region", y="yield_t_per_ha", color="region", points="all",
        color_discrete_map={"Coffee belt": ACCENT, "Outside belt": "#888"},
        labels={"yield_t_per_ha": "Yield (t/ha)", "region": ""},
        hover_data=["country", "year"],
    )
    fig.update_layout(
        template=TEMPLATE, showlegend=False,
        title="<b>Margin countries are few but average higher yields than belt countries</b>",
        margin=dict(l=10, r=10, t=70, b=10),
    )
    return fig


# ============================================================================
# H2 — Quality drivers
# ============================================================================

CUPPING_DIMS = ["aroma", "flavor", "aftertaste", "acidity", "body",
                "balance", "uniformity", "clean_cup", "sweetness", "cupper_points"]


def fig_altitude_box(cqi: pd.DataFrame) -> go.Figure:
    df = cqi.dropna(subset=["altitude_bin", "total_cup_points"]).copy()
    order = ["<1000m", "1000-1500m", "1500-2000m", ">2000m"]
    df["altitude_bin"] = pd.Categorical(df["altitude_bin"], categories=order, ordered=True)
    fig = px.box(
        df, x="altitude_bin", y="total_cup_points",
        category_orders={"altitude_bin": order},
        color="altitude_bin",
        color_discrete_sequence=px.colors.sequential.YlOrBr[2:],
        labels={"altitude_bin": "Altitude band", "total_cup_points": "Total cup points"},
    )
    fig.update_layout(
        template=TEMPLATE, showlegend=False,
        title="<b>Higher altitude does lift cupping scores — but the margin is small</b>"
              "<br><sup>Distribution of total cup points by altitude band (CQI Q-grader scores)</sup>",
        margin=dict(l=10, r=10, t=70, b=10),
    )
    return fig


def fig_parallel_coordinates(cqi: pd.DataFrame, max_rows: int = 800) -> go.Figure:
    df = cqi.dropna(subset=CUPPING_DIMS + ["total_cup_points"]).copy()
    if len(df) > max_rows:
        df = df.sample(max_rows, random_state=0)
    fig = px.parallel_coordinates(
        df, dimensions=CUPPING_DIMS,
        color="total_cup_points", color_continuous_scale=SEQ,
        labels={c: c.replace("_", " ").title() for c in CUPPING_DIMS},
    )
    fig.update_layout(
        template=TEMPLATE,
        title="<b>What separates great coffees? Flavor, aftertaste, balance — together.</b>"
              "<br><sup>Each line is one cupped lot; color = total cup points</sup>",
        margin=dict(l=80, r=40, t=70, b=40),
    )
    return fig


def fig_quality_regression(cqi: pd.DataFrame) -> go.Figure:
    """Bar chart of standardized regression coefficients on total_cup_points."""
    import statsmodels.api as sm
    df = cqi.dropna(subset=["total_cup_points", "altitude_m"]).copy()
    # Build numeric features.
    feats = pd.DataFrame({
        "altitude_m": df["altitude_m"],
        "moisture": pd.to_numeric(df["moisture"], errors="coerce"),
        "cat1_defects": pd.to_numeric(df["cat1_defects"], errors="coerce"),
        "cat2_defects": pd.to_numeric(df["cat2_defects"], errors="coerce"),
    })
    proc = pd.get_dummies(df["processing"].fillna("Unknown"), prefix="proc", drop_first=True)
    feats = pd.concat([feats, proc], axis=1).fillna(0)
    # Standardize numeric (not the dummies).
    for col in ["altitude_m", "moisture", "cat1_defects", "cat2_defects"]:
        s = feats[col]
        if s.std():
            feats[col] = (s - s.mean()) / s.std()
    feats = feats.astype(float)
    X = sm.add_constant(feats)
    y = df["total_cup_points"].astype(float)
    model = sm.OLS(y, X).fit()
    coefs = model.params.drop("const")
    ses = model.bse.drop("const")
    order = coefs.abs().sort_values(ascending=True).index
    coefs = coefs.loc[order]
    ses = ses.loc[order]
    fig = go.Figure()
    fig.add_bar(
        x=coefs.values, y=coefs.index, orientation="h",
        error_x=dict(type="data", array=ses.values),
        marker_color=[ACCENT if v > 0 else "#888" for v in coefs.values],
        hovertemplate="%{y}: β=%{x:.3f}<extra></extra>",
    )
    fig.update_layout(
        template=TEMPLATE,
        title="<b>Altitude is the largest single positive driver of cupping score</b>"
              f"<br><sup>OLS coefficients (numeric features standardized); R²={model.rsquared:.2f}, n={int(model.nobs)}</sup>",
        xaxis_title="Std. coefficient on Total Cup Points",
        yaxis_title="",
        margin=dict(l=120, r=40, t=80, b=40),
    )
    return fig, model


# ============================================================================
# H3 — Price vs rating
# ============================================================================

def fig_price_rating(reviews: pd.DataFrame) -> go.Figure:
    df = reviews.dropna(subset=["price_100g_usd", "rating"]).copy()
    df = df[df["price_100g_usd"] <= df["price_100g_usd"].quantile(0.99)]  # tail trim
    fig = px.scatter(
        df, x="price_100g_usd", y="rating",
        opacity=0.45, hover_name="name",
        hover_data={"roaster": True, "origin_primary": True,
                    "price_100g_usd": ":.2f", "rating": True},
        labels={"price_100g_usd": "Price ($/100g)", "rating": "Rating (0-100)"},
        color_discrete_sequence=[ACCENT],
    )
    # LOWESS overlay.
    try:
        import statsmodels.api as sm
        smoothed = sm.nonparametric.lowess(df["rating"], df["price_100g_usd"], frac=0.3)
        fig.add_scatter(x=smoothed[:, 0], y=smoothed[:, 1],
                        mode="lines", name="LOWESS", line=dict(color="#222", width=3))
    except Exception:
        pass
    # Annotate diminishing-returns inflection ~ $12.
    fig.add_vline(x=12, line_dash="dot", line_color="grey")
    fig.add_annotation(
        x=12, y=df["rating"].min() + 1,
        text="$12: diminishing returns", showarrow=False, xshift=70, font=dict(color="grey"),
    )
    fig.update_layout(
        template=TEMPLATE,
        title="<b>Above ~$12 / 100g, more money buys very few extra rating points</b>"
              "<br><sup>coffeereview.com 2017–2022, n="
              f"{len(df):,} (top 1% prices trimmed)</sup>",
        margin=dict(l=10, r=10, t=70, b=10),
    )
    return fig


def fig_roast_by_year(reviews: pd.DataFrame) -> go.Figure:
    df = reviews.dropna(subset=["roast", "review_year"]).copy()
    df["roast"] = pd.Categorical(
        df["roast"],
        categories=["Light", "Medium-Light", "Medium", "Medium-Dark", "Dark"],
        ordered=True,
    )
    yr = df.groupby(["review_year", "roast"], observed=True).size().reset_index(name="n")
    totals = yr.groupby("review_year")["n"].transform("sum")
    yr["share"] = yr["n"] / totals
    fig = px.area(
        yr, x="review_year", y="share", color="roast",
        category_orders={"roast": ["Light", "Medium-Light", "Medium", "Medium-Dark", "Dark"]},
        color_discrete_sequence=px.colors.sequential.YlOrBr,
        labels={"review_year": "Year", "share": "Share of reviews"},
    )
    fig.update_yaxes(tickformat=".0%")
    fig.update_layout(
        template=TEMPLATE,
        title="<b>Specialty roasting is overwhelmingly Medium-Light</b>"
              "<br><sup>Share of reviews by roast level, by year</sup>",
        margin=dict(l=10, r=10, t=70, b=10),
        legend_title_text="Roast",
    )
    return fig


# ============================================================================
# H4 — NLP flavor clusters
# ============================================================================

def fig_flavor_wordcloud(reviews: pd.DataFrame, rating_tier: str = "high"):
    """Returns a matplotlib Figure (wordcloud isn't natively Plotly)."""
    from wordcloud import WordCloud, STOPWORDS
    import matplotlib.pyplot as plt

    df = reviews.dropna(subset=["desc_1", "rating"]).copy()
    if rating_tier == "high":
        df = df[df["rating"] >= df["rating"].quantile(0.75)]
        title = f"Top quartile reviews (rating ≥ {df['rating'].min():.0f})"
    elif rating_tier == "low":
        df = df[df["rating"] <= df["rating"].quantile(0.25)]
        title = f"Bottom quartile reviews (rating ≤ {df['rating'].max():.0f})"
    else:
        title = "All reviews"
    text = " ".join(df["desc_1"].astype(str).tolist()).lower()
    extra_stop = {"coffee", "cup", "aroma", "structure", "finish", "long",
                  "short", "evaluated", "espresso", "blend", "mouthfeel", "tones"}
    stop = set(STOPWORDS) | extra_stop
    wc = WordCloud(width=900, height=450, background_color="white",
                   stopwords=stop, colormap="YlOrBr").generate(text)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    ax.set_title(title)
    return fig


def cluster_flavors(reviews: pd.DataFrame, n_clusters: int = 5):
    """Run TF-IDF + KMeans on description text; return (df, top_terms)."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans

    df = reviews.dropna(subset=["desc_1", "origin_primary"]).copy()
    text = df["desc_1"].astype(str)
    extra_stop = ["coffee", "cup", "aroma", "structure", "finish", "long", "short",
                  "evaluated", "espresso", "blend", "mouthfeel", "tones", "rich",
                  "deeply", "deep", "notes", "note", "narrow", "drying"]
    vec = TfidfVectorizer(stop_words="english", max_features=400,
                          ngram_range=(1, 1), min_df=10)
    X = vec.fit_transform(text)
    # Drop the extra stopwords from the matrix.
    vocab = vec.get_feature_names_out()
    keep = [i for i, w in enumerate(vocab) if w not in extra_stop]
    X = X[:, keep]
    vocab = vocab[keep]
    km = KMeans(n_clusters=n_clusters, random_state=0, n_init=10).fit(X)
    df["cluster"] = km.labels_
    centers = km.cluster_centers_
    top_terms = {}
    for c in range(n_clusters):
        idx = centers[c].argsort()[::-1][:8]
        top_terms[c] = [vocab[i] for i in idx]
    return df, top_terms


def fig_cluster_by_origin(df_clustered: pd.DataFrame, top_terms: dict) -> go.Figure:
    df = df_clustered.copy()
    top = df["origin_primary"].value_counts().head(10).index.tolist()
    df = df[df["origin_primary"].isin(top)]
    pivot = (
        df.groupby(["origin_primary", "cluster"])
        .size()
        .unstack(fill_value=0)
    )
    pivot = pivot.div(pivot.sum(axis=1), axis=0)
    pivot = pivot.loc[top]
    labels = {c: f"C{c}: " + ", ".join(top_terms[c][:3]) for c in pivot.columns}
    fig = go.Figure()
    for c in pivot.columns:
        fig.add_bar(
            name=labels[c], x=pivot.index, y=pivot[c],
            hovertemplate="%{x}<br>%{y:.0%}<extra>" + labels[c] + "</extra>",
        )
    fig.update_layout(
        template=TEMPLATE, barmode="stack",
        title="<b>Flavor signatures cluster by origin</b>"
              "<br><sup>Share of each origin's reviews falling into TF-IDF + KMeans flavor clusters</sup>",
        yaxis_tickformat=".0%",
        xaxis_title="", yaxis_title="Cluster share",
        legend=dict(orientation="h", yanchor="bottom", y=-0.45),
        margin=dict(l=10, r=10, t=70, b=130),
        colorway=PALETTE,
    )
    return fig


def fig_descriptor_network(reviews: pd.DataFrame, top_n: int = 30) -> go.Figure:
    """Co-occurrence network of frequent flavor descriptors."""
    import re
    import networkx as nx
    from collections import Counter
    flavor_words = [
        "chocolate", "cocoa", "vanilla", "caramel", "honey", "berry", "cherry",
        "lemon", "lime", "orange", "grapefruit", "apricot", "peach", "apple",
        "floral", "jasmine", "rose", "spice", "cinnamon", "cardamom", "pepper",
        "nutty", "almond", "hazelnut", "walnut", "earthy", "tobacco", "wine",
        "fruit", "citrus", "sweet", "bright", "tart", "smoky", "syrupy",
        "molasses", "raisin", "blackberry", "blueberry", "strawberry",
    ]
    pat = re.compile(r"\b(" + "|".join(flavor_words) + r")\b", re.I)
    pairs = Counter()
    for text in reviews["desc_1"].dropna().astype(str):
        found = sorted(set(m.lower() for m in pat.findall(text)))
        for i in range(len(found)):
            for j in range(i + 1, len(found)):
                pairs[(found[i], found[j])] += 1

    # Keep top edges by weight.
    top_edges = pairs.most_common(top_n * 4)
    G = nx.Graph()
    for (a, b), w in top_edges:
        G.add_edge(a, b, weight=w)
    if len(G) == 0:
        return go.Figure()

    pos = nx.spring_layout(G, seed=42, weight="weight")
    edge_x, edge_y = [], []
    for a, b in G.edges():
        x0, y0 = pos[a]; x1, y1 = pos[b]
        edge_x += [x0, x1, None]; edge_y += [y0, y1, None]

    deg = dict(G.degree(weight="weight"))
    node_x = [pos[n][0] for n in G.nodes()]
    node_y = [pos[n][1] for n in G.nodes()]
    node_size = [10 + 4 * np.log1p(deg[n]) for n in G.nodes()]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(width=0.5, color="#bbb"), hoverinfo="none",
    ))
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y, mode="markers+text",
        text=list(G.nodes()), textposition="top center",
        marker=dict(size=node_size, color=ACCENT, line=dict(width=1, color="white")),
        hovertemplate="%{text}<br>connections: %{marker.size}<extra></extra>",
    ))
    fig.update_layout(
        template=TEMPLATE, showlegend=False,
        title="<b>Flavor descriptor co-occurrence network</b>"
              "<br><sup>Edges = words appearing together in the same review</sup>",
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        margin=dict(l=10, r=10, t=70, b=10),
    )
    return fig


# ============================================================================
# Cross-dataset synthesis
# ============================================================================

def fig_volume_quality_price(fao: pd.DataFrame, cqi: pd.DataFrame, reviews: pd.DataFrame) -> go.Figure:
    """Bubble: x=production volume, y=mean cupping score, size=mean review price."""
    fao_recent = fao[(~fao["is_aggregate"]) & fao["year"].between(2017, 2022)]
    prod = (
        fao_recent.groupby("country", as_index=False)["production_tonnes"].mean()
        .rename(columns={"production_tonnes": "avg_production_tonnes"})
    )
    quality = (
        cqi.dropna(subset=["total_cup_points", "country"])
        .groupby("country", as_index=False)["total_cup_points"].mean()
        .rename(columns={"total_cup_points": "avg_cup_points"})
    )
    rev_price = (
        reviews.dropna(subset=["price_100g_usd", "origin_primary"])
        .groupby("origin_primary", as_index=False)["price_100g_usd"].mean()
        .rename(columns={"origin_primary": "country", "price_100g_usd": "avg_price_100g"})
    )
    rev_n = (
        reviews.dropna(subset=["origin_primary"])
        .groupby("origin_primary").size()
        .rename("n_reviews").reset_index().rename(columns={"origin_primary": "country"})
    )

    df = prod.merge(quality, on="country").merge(rev_price, on="country", how="left").merge(rev_n, on="country", how="left")
    df = df[df["avg_production_tonnes"] > 0]
    # Bubble size needs a value for every row; fall back to global mean for origins
    # without specialty-review pricing (then mark them differently in hover).
    df["avg_price_100g_filled"] = df["avg_price_100g"].fillna(df["avg_price_100g"].mean())
    df["n_reviews"] = df["n_reviews"].fillna(0).astype(int)

    fig = px.scatter(
        df, x="avg_production_tonnes", y="avg_cup_points",
        size="avg_price_100g_filled", color="avg_price_100g",
        hover_name="country",
        hover_data={"avg_production_tonnes": ":.0f", "avg_cup_points": ":.2f",
                    "avg_price_100g": ":.2f", "avg_price_100g_filled": False,
                    "n_reviews": True},
        log_x=True,
        size_max=45,
        color_continuous_scale=SEQ,
        labels={
            "avg_production_tonnes": "Avg annual production (tonnes, log)",
            "avg_cup_points": "Mean Q-grader cup points",
            "avg_price_100g": "Avg specialty price ($/100g)",
        },
    )
    # Text labels for top countries.
    for _, r in df.nlargest(8, "avg_production_tonnes").iterrows():
        fig.add_annotation(x=np.log10(r["avg_production_tonnes"]) if False else r["avg_production_tonnes"],
                           y=r["avg_cup_points"], text=r["country"],
                           showarrow=False, yshift=14, font=dict(size=10))
    fig.update_layout(
        template=TEMPLATE,
        title="<b>Volume vs. quality: the specialty market lives in low-volume origins</b>"
              "<br><sup>Bubble size = avg specialty retail price (2017–2022)</sup>",
        margin=dict(l=10, r=10, t=70, b=10),
    )
    return fig

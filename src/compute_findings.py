"""Compute the headline numbers cited in the writeup and slides.

Run: python -m src.compute_findings
Outputs: docs/findings.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
DOCS = ROOT / "docs"
DOCS.mkdir(exist_ok=True)


def main():
    fao = pd.read_parquet(PROC / "fao.parquet")
    cqi = pd.read_parquet(PROC / "cqi.parquet")
    rev = pd.read_parquet(PROC / "reviews.parquet")

    out: dict = {}

    # H1 -------------------------------------------------------------------
    sub = fao[(~fao["is_aggregate"]) & fao["yield_t_per_ha"].notna() & fao["lat"].notna()
              & fao["year"].between(2010, 2022)]
    belt = sub[sub["lat"].abs() <= 23.5]["yield_t_per_ha"]
    margin = sub[sub["lat"].abs() > 23.5]["yield_t_per_ha"]
    from scipy import stats
    t, p = stats.ttest_ind(belt, margin, equal_var=False)
    out["h1"] = {
        "belt_mean_yield": float(belt.mean()),
        "belt_n": int(belt.size),
        "margin_mean_yield": float(margin.mean()),
        "margin_n": int(margin.size),
        "diff": float(belt.mean() - margin.mean()),
        "welch_t": float(t),
        "welch_p": float(p),
    }
    # Top producers 2022.
    p22 = (fao[(~fao["is_aggregate"]) & (fao["year"] == 2022)]
           .nlargest(5, "production_tonnes")[["country", "production_tonnes"]])
    out["h1"]["top5_producers_2022"] = [
        {"country": r.country, "tonnes": float(r.production_tonnes)} for r in p22.itertuples()
    ]
    total22 = fao[(~fao["is_aggregate"]) & (fao["year"] == 2022)]["production_tonnes"].sum()
    out["h1"]["world_total_2022_tonnes"] = float(total22)
    out["h1"]["top5_share_2022"] = float(p22["production_tonnes"].sum() / total22)

    # H2 -------------------------------------------------------------------
    cqi_alt = cqi.dropna(subset=["altitude_bin", "total_cup_points"])
    means = cqi_alt.groupby("altitude_bin", observed=True)["total_cup_points"].mean()
    out["h2"] = {
        "altitude_means": {str(k): float(v) for k, v in means.items()},
        "n_lots": int(len(cqi)),
        "n_with_altitude": int(cqi["altitude_m"].notna().sum()),
    }
    # Re-run regression for stable numbers.
    import statsmodels.api as sm
    df = cqi.dropna(subset=["total_cup_points", "altitude_m"]).copy()
    feats = pd.DataFrame({
        "altitude_m": df["altitude_m"],
        "moisture": pd.to_numeric(df["moisture"], errors="coerce"),
        "cat1_defects": pd.to_numeric(df["cat1_defects"], errors="coerce"),
        "cat2_defects": pd.to_numeric(df["cat2_defects"], errors="coerce"),
    })
    proc = pd.get_dummies(df["processing"].fillna("Unknown"), prefix="proc", drop_first=True)
    feats = pd.concat([feats, proc], axis=1).fillna(0)
    for col in ["altitude_m", "moisture", "cat1_defects", "cat2_defects"]:
        s = feats[col]
        if s.std():
            feats[col] = (s - s.mean()) / s.std()
    feats = feats.astype(float)
    X = sm.add_constant(feats)
    y = df["total_cup_points"].astype(float)
    model = sm.OLS(y, X).fit()
    out["h2"]["regression_r2"] = float(model.rsquared)
    out["h2"]["regression_n"] = int(model.nobs)
    out["h2"]["altitude_beta"] = float(model.params.get("altitude_m", np.nan))
    out["h2"]["altitude_p"] = float(model.pvalues.get("altitude_m", np.nan))
    out["h2"]["cat1_defects_beta"] = float(model.params.get("cat1_defects", np.nan))

    # H3 -------------------------------------------------------------------
    r = rev.dropna(subset=["price_100g_usd", "rating"])
    bands = pd.cut(r["price_100g_usd"], bins=[0, 5, 8, 12, 20, 1000],
                   labels=["<$5", "$5-8", "$8-12", "$12-20", ">$20"])
    band_mean = r.groupby(bands, observed=True)["rating"].mean()
    out["h3"] = {
        "n_reviews": int(len(r)),
        "band_means": {str(k): float(v) for k, v in band_mean.items()},
        "spearman_corr": float(r["price_100g_usd"].corr(r["rating"], method="spearman")),
        "pearson_corr_log": float(np.log(r["price_100g_usd"]).corr(r["rating"])),
    }

    # H4 -------------------------------------------------------------------
    out["h4"] = {
        "n_reviews_with_origin": int(rev["origin_primary"].notna().sum()),
        "top10_origins": rev["origin_primary"].value_counts().head(10).to_dict(),
    }

    # Synthesis -----------------------------------------------------------
    fao_recent = fao[(~fao["is_aggregate"]) & fao["year"].between(2017, 2022)]
    prod = fao_recent.groupby("country")["production_tonnes"].mean()
    quality = cqi.dropna(subset=["total_cup_points"]).groupby("country")["total_cup_points"].mean()
    price = (rev.dropna(subset=["price_100g_usd", "origin_primary"])
             .groupby("origin_primary")["price_100g_usd"].mean())
    join = pd.DataFrame({"prod": prod, "quality": quality, "price": price}).dropna()
    out["synthesis"] = {
        "n_joined_countries": int(len(join)),
        "corr_volume_quality_spearman": float(join["prod"].corr(join["quality"], method="spearman")),
        "corr_volume_price_spearman": float(join["prod"].corr(join["price"], method="spearman")),
        "corr_quality_price_spearman": float(join["quality"].corr(join["price"], method="spearman")),
    }

    DOCS.joinpath("findings.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()

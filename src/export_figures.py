"""Export every figure to PNG so the slide deck and write-up can embed them.

Run: python -m src.export_figures
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src import figures as F

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
OUT = ROOT / "docs" / "img"
OUT.mkdir(parents=True, exist_ok=True)


def main():
    fao = pd.read_parquet(PROC / "fao.parquet")
    cqi = pd.read_parquet(PROC / "cqi.parquet")
    rev = pd.read_parquet(PROC / "reviews.parquet")

    W, H = 1600, 900

    def save(fig, name):
        path = OUT / f"{name}.png"
        fig.write_image(path, width=W, height=H, scale=1)
        print(f"  wrote {path}")

    print("Exporting Plotly figures …")
    save(F.fig_production_choropleth(fao, 2022), "h1_choropleth_2022")
    save(F.fig_yield_vs_latitude(fao), "h1_yield_lat")
    save(F.fig_belt_vs_margin_box(fao), "h1_belt_box")
    save(F.fig_altitude_box(cqi), "h2_altitude_box")
    save(F.fig_parallel_coordinates(cqi), "h2_parallel")
    fig, _ = F.fig_quality_regression(cqi)
    save(fig, "h2_regression")
    save(F.fig_price_rating(rev), "h3_price_rating")
    save(F.fig_roast_by_year(rev), "h3_roast_by_year")
    df_c, terms = F.cluster_flavors(rev)
    save(F.fig_cluster_by_origin(df_c, terms), "h4_clusters")
    save(F.fig_descriptor_network(rev), "h4_network")
    save(F.fig_volume_quality_price(fao, cqi, rev), "synthesis_bubble")

    print("Exporting matplotlib word clouds …")
    F.fig_flavor_wordcloud(rev, "high").savefig(OUT / "h4_wc_high.png", bbox_inches="tight", dpi=150)
    F.fig_flavor_wordcloud(rev, "low").savefig(OUT / "h4_wc_low.png", bbox_inches="tight", dpi=150)

    print(f"\nAll PNGs in: {OUT}")


if __name__ == "__main__":
    main()

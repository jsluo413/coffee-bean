"""Load, clean, and join the three coffee datasets + FAO supplemental.

Outputs parquet files to data/processed/ so the Streamlit app can load fast.
Run: python -m src.data_prep
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)


# ---------- helpers ----------------------------------------------------------

def _strip(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip()


# Map the messy country strings appearing across the three datasets to a
# canonical name we use everywhere.
COUNTRY_CANONICAL = {
    "Tanzania, United Republic Of": "Tanzania",
    "United Republic of Tanzania": "Tanzania",
    "Cote d?Ivoire": "Cote d'Ivoire",
    "Côte d'Ivoire": "Cote d'Ivoire",
    "Cote d'Ivoire": "Cote d'Ivoire",
    "Lao People's Democratic Republic": "Laos",
    "Lao": "Laos",
    "Viet Nam": "Vietnam",
    "Bolivia (Plurinational State of)": "Bolivia",
    "Venezuela (Bolivarian Republic of)": "Venezuela",
    "United States Of America": "United States",
    "United States of America": "United States",
    "USA": "United States",
    "U.S.A.": "United States",
    "United States (Hawaii)": "United States",
    "Hawaii": "United States",
    "Papua New Guinea (PNG)": "Papua New Guinea",
    "Taiwan, Province of China": "Taiwan",
    "Taiwan (Province of China)": "Taiwan",
    "Democratic Republic of the Congo": "DR Congo",
    "Congo, Democratic Republic of the": "DR Congo",
    "Congo, The Democratic Republic Of The": "DR Congo",
    "Myanmar (formerly Burma)": "Myanmar",
}


def canon_country(s: pd.Series) -> pd.Series:
    s = _strip(s).replace({"nan": np.nan, "": np.nan})
    s = s.replace(COUNTRY_CANONICAL)
    return s


# ---------- FAO production ---------------------------------------------------

def load_fao_production() -> pd.DataFrame:
    df = pd.read_csv(RAW / "coffee-bean-production" / "coffee-bean-production.csv")
    df = df.rename(columns={
        "Entity": "country",
        "Code": "iso3",
        "Year": "year",
        "Green coffee - Production (tonnes)": "production_tonnes",
    })
    df["country"] = canon_country(df["country"])
    return df


def load_fao_yield() -> pd.DataFrame:
    df = pd.read_csv(RAW / "fao-supplemental" / "yield.csv")
    df = df.rename(columns={
        "Entity": "country",
        "Code": "iso3",
        "Year": "year",
        "Green coffee - Yield (tonnes per hectare)": "yield_t_per_ha",
    })
    df["country"] = canon_country(df["country"])
    return df


def load_country_centroids() -> pd.DataFrame:
    df = pd.read_csv(RAW / "fao-supplemental" / "country_centroids.csv")
    df = df.rename(columns={
        "country": "iso2",
        "latitude": "lat",
        "longitude": "lon",
        "name": "country_name_iso",
    })
    return df


def build_fao() -> pd.DataFrame:
    """Country-year FAO panel with production, yield, derived area, lat/lon."""
    prod = load_fao_production()
    yld = load_fao_yield()

    fao = prod.merge(yld, on=["country", "iso3", "year"], how="outer")
    # Derive area (ha) where both numbers exist:
    with np.errstate(divide="ignore", invalid="ignore"):
        fao["area_ha"] = np.where(
            (fao["yield_t_per_ha"] > 0) & fao["production_tonnes"].notna(),
            fao["production_tonnes"] / fao["yield_t_per_ha"],
            np.nan,
        )

    # Drop region aggregates from country-level work. OWID prefixes them with
    # OWID_; FAOSTAT also publishes named aggregates like "Africa (FAO)" with
    # no ISO3, plus the special "(FAO)" suffix for many groupings.
    fao["is_aggregate"] = (
        fao["iso3"].fillna("").str.startswith("OWID_")
        | fao["country"].fillna("").str.contains(r"\(FAO\)", regex=True)
        | fao["iso3"].isna()
    )

    # Country-level lat/lon via iso3 -> iso2 mapping using pycountry.
    try:
        import pycountry
        iso3_to_iso2 = {c.alpha_3: c.alpha_2 for c in pycountry.countries}
    except Exception:
        iso3_to_iso2 = {}
    fao["iso2"] = fao["iso3"].map(iso3_to_iso2)

    cents = load_country_centroids()
    fao = fao.merge(cents[["iso2", "lat", "lon"]], on="iso2", how="left")

    # Coffee belt flag: tropics 23.5N to 23.5S
    fao["coffee_belt"] = fao["lat"].abs() <= 23.5

    return fao


# ---------- CQI quality ------------------------------------------------------

ALT_RE = re.compile(r"(\d{2,5}(?:\.\d+)?)")


def parse_altitude(value):
    """Return mean meters from messy 'Altitude' string when possible."""
    if pd.isna(value):
        return np.nan
    s = str(value).lower().replace(",", "")
    nums = [float(m) for m in ALT_RE.findall(s)]
    if not nums:
        return np.nan
    # Some are in feet -> convert to meters when 'ft' or 'feet' appears.
    if "ft" in s or "feet" in s:
        nums = [n * 0.3048 for n in nums]
    # Implausible (>9000 m) likely feet without label.
    nums = [n for n in nums if 0 < n <= 9000]
    if not nums:
        return np.nan
    return float(np.mean(nums))


def load_cqi() -> pd.DataFrame:
    df = pd.read_csv(RAW / "coffee-quality" / "merged_data_cleaned.csv")
    rename = {
        "Country.of.Origin": "country",
        "Total.Cup.Points": "total_cup_points",
        "Aroma": "aroma", "Flavor": "flavor", "Aftertaste": "aftertaste",
        "Acidity": "acidity", "Body": "body", "Balance": "balance",
        "Uniformity": "uniformity", "Clean.Cup": "clean_cup",
        "Sweetness": "sweetness", "Cupper.Points": "cupper_points",
        "Variety": "variety", "Processing.Method": "processing",
        "Species": "species", "altitude_mean_meters": "altitude_m_raw",
        "Harvest.Year": "harvest_year_raw",
        "Region": "region", "Color": "color",
        "Category.One.Defects": "cat1_defects",
        "Category.Two.Defects": "cat2_defects",
        "Moisture": "moisture",
    }
    df = df.rename(columns=rename)[list(rename.values())]
    df["country"] = canon_country(df["country"])

    # Parse altitude: prefer the OWID-cleaned mean, else parse the raw 'Altitude'.
    df["altitude_m"] = pd.to_numeric(df["altitude_m_raw"], errors="coerce")
    # Some merged_cleaned rows have absurd altitudes (>9000m); null them.
    df.loc[(df["altitude_m"] <= 0) | (df["altitude_m"] > 9000), "altitude_m"] = np.nan

    # Altitude bins for H2.
    bins = [-np.inf, 1000, 1500, 2000, np.inf]
    labels = ["<1000m", "1000-1500m", "1500-2000m", ">2000m"]
    df["altitude_bin"] = pd.cut(df["altitude_m"], bins=bins, labels=labels)

    # Drop rows where total_cup_points is missing or 0 (a known data-quality issue).
    df = df[df["total_cup_points"].between(50, 100)].copy()

    return df


# ---------- coffeereview.com -------------------------------------------------

# Known coffee-producing countries plus aliases the reviews corpus uses for them.
COUNTRY_KEYWORDS: dict[str, list[str]] = {
    "Ethiopia": ["ethiopia", "yirgacheffe", "sidamo", "sidama", "guji", "harrar", "harar", "kaffa", "limu", "djimma", "jimma", "gedeb", "gedeo", "kochere", "oromia", "shakiso"],
    "Kenya": ["kenya", "nyeri", "kiambu", "kirinyaga"],
    "Colombia": ["colombia", "huila", "narino", "nariño", "cauca", "antioquia", "tolima", "santander"],
    "Guatemala": ["guatemala", "huehuetenango", "antigua", "atitlan", "atitlán", "acatenango", "coban", "cobán"],
    "Costa Rica": ["costa rica", "tarrazu", "tarrazú", "brunca", "tres rios", "central valley", "west valley"],
    "Panama": ["panama", "panamá", "boquete", "volcan", "volcán", "chiriqui", "chiriquí"],
    "Brazil": ["brazil", "minas gerais", "cerrado", "mogiana", "sul de minas", "espirito santo", "espírito santo"],
    "Honduras": ["honduras"],
    "Nicaragua": ["nicaragua"],
    "El Salvador": ["el salvador", "salvador"],
    "Mexico": ["mexico", "méxico", "chiapas", "oaxaca", "veracruz"],
    "Peru": ["peru", "perú", "cajamarca", "chanchamayo"],
    "Bolivia": ["bolivia"],
    "Ecuador": ["ecuador", "loja", "zamora"],
    "Venezuela": ["venezuela"],
    "Indonesia": ["indonesia", "sumatra", "sulawesi", "java", "bali", "flores", "toraja", "mandheling", "gayo", "aceh", "lintong"],
    "Vietnam": ["vietnam", "viet nam"],
    "Yemen": ["yemen"],
    "India": ["india", "mysore", "monsooned malabar"],
    "Thailand": ["thailand"],
    "China": ["china", "yunnan"],
    "Myanmar": ["myanmar", "burma"],
    "Laos": ["laos", "lao"],
    "Papua New Guinea": ["papua new guinea", "png"],
    "Timor-Leste": ["timor", "east timor"],
    "Philippines": ["philippines"],
    "Hawaii": ["hawai", "kona", "kau", "ka'u", "ka u"],
    "Jamaica": ["jamaica", "blue mountain"],
    "Dominican Republic": ["dominican republic"],
    "Haiti": ["haiti"],
    "Puerto Rico": ["puerto rico"],
    "Cuba": ["cuba"],
    "Rwanda": ["rwanda"],
    "Burundi": ["burundi"],
    "Tanzania": ["tanzania", "kilimanjaro"],
    "Uganda": ["uganda"],
    "DR Congo": ["dr congo", "drc", "democratic republic of the congo", "kivu"],
    "Cameroon": ["cameroon"],
    "Cote d'Ivoire": ["ivory coast", "côte d'ivoire", "cote d'ivoire", "cote d ivoire"],
    "Madagascar": ["madagascar"],
    "Malawi": ["malawi"],
    "Zambia": ["zambia"],
    "Zimbabwe": ["zimbabwe"],
    "Australia": ["australia"],
    "Taiwan": ["taiwan"],
    "Nepal": ["nepal"],
}


def detect_country(*texts: str) -> str | None:
    """Find first matching coffee-producing country across the given strings."""
    blob = " ".join(str(t).lower() for t in texts if pd.notna(t))
    if not blob.strip():
        return None
    for country, keywords in COUNTRY_KEYWORDS.items():
        for kw in keywords:
            if kw in blob:
                return country
    return None


def load_reviews() -> pd.DataFrame:
    df = pd.read_csv(RAW / "coffee-reviews" / "coffee_analysis.csv")
    df = df.rename(columns={
        "name": "name", "roaster": "roaster", "roast": "roast",
        "loc_country": "roaster_country",
        "origin_1": "origin_1", "origin_2": "origin_2",
        "100g_USD": "price_100g_usd", "rating": "rating",
        "review_date": "review_date",
        "desc_1": "desc_1", "desc_2": "desc_2", "desc_3": "desc_3",
    })

    df["origin_primary"] = df.apply(
        lambda r: detect_country(r.get("origin_2"), r.get("origin_1"), r.get("name"), r.get("desc_2")),
        axis=1,
    )
    df["price_100g_usd"] = pd.to_numeric(df["price_100g_usd"], errors="coerce")
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df["review_date"] = pd.to_datetime(df["review_date"], errors="coerce")
    df["review_year"] = df["review_date"].dt.year

    # Roast level normalized.
    df["roast"] = df["roast"].astype(str).str.strip().replace({"nan": np.nan})

    df = df[df["rating"].between(50, 100)]
    df = df[df["price_100g_usd"].between(0.1, 500)]

    return df.reset_index(drop=True)


# ---------- entrypoint -------------------------------------------------------

def main():
    fao = build_fao()
    cqi = load_cqi()
    rev = load_reviews()

    fao.to_parquet(OUT / "fao.parquet", index=False)
    cqi.to_parquet(OUT / "cqi.parquet", index=False)
    rev.to_parquet(OUT / "reviews.parquet", index=False)

    print(f"FAO rows: {len(fao):,}  unique countries: {fao['country'].nunique()}")
    print(f"  with lat/lon: {fao['lat'].notna().sum():,}  belt rows: {fao['coffee_belt'].sum():,}")
    print(f"CQI rows: {len(cqi):,}  unique countries: {cqi['country'].nunique()}")
    print(f"  altitude non-null: {cqi['altitude_m'].notna().sum():,}")
    print(f"Reviews rows: {len(rev):,}  unique origins: {rev['origin_primary'].nunique()}")
    print(f"  price non-null: {rev['price_100g_usd'].notna().sum():,}  rating non-null: {rev['rating'].notna().sum():,}")


if __name__ == "__main__":
    main()

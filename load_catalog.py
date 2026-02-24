import pandas as pd

CATALOG_PATH = "data/catalog.csv"


def load_and_clean_catalog(path):
    print("Loading catalog...")
    df = pd.read_csv(path)
    print("Original shape:", df.shape)

    # ── Rename columns to standard names ──────────────────────────────
    df = df.rename(columns={
        "Body (HTML)": "description",
        "Variant Price": "price",
        "Image Src": "image_src",
    })

    # ── Fix prices — forward fill so variants inherit from first row ───
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["price"] = df["price"].replace(0, pd.NA).ffill()

    # ── Forward fill Title and description within Handle groups ────────
    df["Title"] = df["Title"].ffill()
    df["description"] = df["description"].ffill()

    # ── RULE: Use Image Position = 1 as main image ─────────────────────
    if "Image Position" in df.columns:
        df["Image Position"] = pd.to_numeric(df["Image Position"], errors="coerce")
        df_main = df[df["Image Position"] == 1].copy()

        # Fallback: some Handles may have no Image Position = 1 row
        handles_with_main = set(df_main["Handle"].dropna())
        df_fallback = df[~df["Handle"].isin(handles_with_main)].copy()
        df_fallback = df_fallback.drop_duplicates(subset=["Handle"], keep="first")

        df = pd.concat([df_main, df_fallback], ignore_index=True)

    # ── RULE: Group by Handle — one row per product ────────────────────
    df = df.drop_duplicates(subset=["Handle"], keep="first")

    # ── Keep only the columns we need ──────────────────────────────────
    # RULE: Ignore advanced Google Shopping columns
    keep = ["Handle", "Title", "description", "image", "price"]
    df = df[[c for c in keep if c in df.columns]].copy()

    # ── Drop rows with missing or zero price ───────────────────────────
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df[df["price"].notna() & (df["price"] > 0)]

    # ── Drop rows with empty local image path ──────────────────────────
    if "image" in df.columns:
        df["image"] = df["image"].fillna("").astype(str)
        df = df[df["image"].str.strip() != ""]

    # ── Remove rug pads — accessories, not rugs ────────────────────────
    df = df[~df["Title"].str.lower().str.contains("rug pad", na=False)]

    # ── Fill remaining NaNs ────────────────────────────────────────────
    df["description"] = df["description"].fillna("")
    df["Title"] = df["Title"].fillna("")

    print("Final shape:", df.shape)
    print("Sample rows:")
    print(df[["Handle", "Title", "image", "price"]].head(5))
    return df.reset_index(drop=True)


if __name__ == "__main__":
    catalog = load_and_clean_catalog(CATALOG_PATH)
    print("\n✅ Catalog loaded successfully!")
    print("Total products:", len(catalog))
    print("\nAll prices in catalog:")
    print(catalog["price"].value_counts().sort_index())

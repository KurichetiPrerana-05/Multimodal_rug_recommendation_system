import pandas as pd

CATALOG_PATH = "data/catalog.csv"

def load_and_clean_catalog(path):
    print("Loading catalog...")
    df = pd.read_csv(path)

    print("Original shape:", df.shape)
    print("Columns:", df.columns.tolist())

    if "image" not in df.columns:
        raise ValueError("CSV does not contain 'image' column with local image paths.")

    # Normalize column names first
    if "Body (HTML)" in df.columns:
        df = df.rename(columns={"Body (HTML)": "description"})
    if "Variant Price" in df.columns:
        df = df.rename(columns={"Variant Price": "price"})

    # Keep useful columns
    keep_cols = []
    for col in ["Handle", "Title", "description", "image", "price"]:
        if col in df.columns:
            keep_cols.append(col)
    df = df[keep_cols].copy()

    # Fix prices — forward fill so variants inherit price from first row
    if "price" in df.columns:
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        df["price"] = df["price"].replace(0, pd.NA)
        df["price"] = df["price"].ffill()

    # ── KEY FIX: deduplicate by Handle, keep first row per product ──
    # This ensures Title, description, and image are all populated
    if "Handle" in df.columns:
        # Forward fill Title and description within each Handle group
        df["Title"] = df["Title"].ffill()
        df["description"] = df["description"].ffill()

        # Keep only the first row per Handle (main image, base price)
        df = df.drop_duplicates(subset=["Handle"], keep="first")

    # Drop rows with missing or zero price
    if "price" in df.columns:
        df = df[df["price"].notna() & (df["price"] > 0)]

    # Drop rows with empty image path
    if "image" in df.columns:
        df["image"] = df["image"].fillna("")
        df = df[df["image"].str.strip() != ""]

    # Fill remaining NaNs
    df["description"] = df["description"].fillna("")
    df["Title"] = df["Title"].fillna("")

    print("Final shape:", df.shape)
    print("Final columns:", df.columns.tolist())
    print("\nSample rows:")
    print(df.head(5))

    return df.reset_index(drop=True)


if __name__ == "__main__":
    catalog = load_and_clean_catalog(CATALOG_PATH)
    print("\n✅ Catalog loaded successfully!")
    print("Total products:", len(catalog))
import os
import pandas as pd
import requests
from tqdm import tqdm
from urllib.parse import urlparse

CATALOG_PATH = "data/catalog.csv"
OUTPUT_DIR = "data/rugs"
TIMEOUT = 20

os.makedirs(OUTPUT_DIR, exist_ok=True)

def find_image_column(df):
    candidates = ["image", "Image Src", "Variant Image"]
    for c in candidates:
        if c in df.columns:
            return c
    return None

def safe_filename(url, idx):
    parsed = urlparse(url)
    name = os.path.basename(parsed.path)
    if not name or "." not in name:
        name = f"rug_{idx}.jpg"
    return f"{idx:04d}_{name}"

def download_image(url, path):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, stream=True, timeout=TIMEOUT, headers=headers)
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"⚠️ Failed: {url} ({e})")
        return False

def main():
    df = pd.read_csv(CATALOG_PATH)

    img_col = find_image_column(df)
    if img_col is None:
        raise ValueError("Could not find image column. Tried: image, Image Src, Variant Image")

    print(f"Using image column: {img_col}")

    new_paths = []
    success = 0
    fail = 0

    print("Downloading rug images...")

    urls = df[img_col].tolist()

    for idx, url in tqdm(list(enumerate(urls))):
        if not isinstance(url, str) or not url.startswith("http"):
            new_paths.append("")
            fail += 1
            continue

        fname = safe_filename(url, idx)
        out_path = os.path.join(OUTPUT_DIR, fname)

        # If already exists, skip download
        if os.path.exists(out_path):
            new_paths.append(out_path.replace("\\", "/"))
            success += 1
            continue

        ok = download_image(url, out_path)
        if ok:
            new_paths.append(out_path.replace("\\", "/"))
            success += 1
        else:
            new_paths.append("")
            fail += 1

    # Write local paths to a unified column called "image"
    df["image"] = new_paths

    backup_path = CATALOG_PATH.replace(".csv", "_backup.csv")
    df.to_csv(backup_path, index=False)
    df.to_csv(CATALOG_PATH, index=False)

    print("\n✅ Done!")
    print(f"Downloaded: {success}")
    print(f"Failed: {fail}")
    print(f"Backup saved as: {backup_path}")
    print(f"Images saved in: {OUTPUT_DIR}")
    print("CSV updated with local paths in column: image")

if __name__ == "__main__":
    main()
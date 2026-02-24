from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import shutil
import os
import pandas as pd

from load_catalog import load_and_clean_catalog
from search.multimodal_search import MultimodalSearchEngine
from search.structured_search import StructuredSearchEngine

app = FastAPI()

# Serve rug images as static files
app.mount("/images", StaticFiles(directory="data/rugs"), name="images")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("Loading catalog and models...")
catalog = load_and_clean_catalog("data/catalog.csv")
engine = MultimodalSearchEngine(catalog)
structured_engine = StructuredSearchEngine(catalog)
print("Backend ready.")


@app.post("/search/multimodal")
async def search_multimodal(
    image: UploadFile = File(None),
    text_query: str = Form(None),
    max_price: float = Form(None),
    min_price: float = Form(None),
    top_k: int = Form(5),
    model_type: str = Form("clip"),  # "clip", "sbert", or "structured"
):
    tq = text_query.strip() if text_query else None

    # Save temp image if provided
    temp_path = None
    if image is not None:
        temp_path = "data/_temp_query.jpg"
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(image.file, f)

    parsed_info = None

    # -----------------------------
    # Choose model
    # -----------------------------
    if model_type == "structured":
        if not tq:
            return {"results": [], "parsed_query": None}

        results, parsed_info = structured_engine.search(
            query=tq,
            top_k=top_k,
            max_price=max_price,
            min_price=min_price,
        )

    elif model_type == "sbert":
        if not tq:
            return {"results": [], "parsed_query": None}

        results = engine.search_sbert(
            text_query=tq,
            top_k=top_k,
            max_price=max_price,
            min_price=min_price,
        )

    elif model_type == "clip":
        if temp_path is None:
            return {"results": [], "parsed_query": None}

        results = engine.search_clip(
            room_image_path=temp_path,
            text_query=tq,
            top_k=top_k,
            max_price=max_price,
            min_price=min_price,
        )

    else:
        raise HTTPException(status_code=400, detail="Invalid model type. Use 'clip', 'sbert', or 'structured'.")

    # -----------------------------
    # Debug
    # -----------------------------
    print("\n==============================")
    print("RAW RESULTS FROM ENGINE:")
    print(results)
    print("==============================\n")

    if results is None or len(results) == 0:
        return {"results": [], "parsed_query": parsed_info}

    # -----------------------------
    # Build JSON output
    # -----------------------------
    output = []

    for _, row in results.iterrows():
        # Final safety net — skip zero/missing price rows
        price = row.get("price", None)
        if price is None or pd.isna(price) or float(price) <= 0:
            continue

        title = (
            str(row["Title"]).strip()
            if "Title" in row and pd.notna(row["Title"]) and str(row["Title"]).strip() != ""
            else str(row.get("Handle", "Unknown Rug"))
        )

        price = float(price)
        score = float(row["score"]) if "score" in row and pd.notna(row["score"]) else 0.0

        raw_image_path = str(row["image"]) if "image" in row and pd.notna(row["image"]) else ""
        if raw_image_path:
            filename = os.path.basename(raw_image_path)
            image_url = f"/images/{filename}"
        else:
            image_url = ""

        # Why text
        if model_type == "clip":
            why_text = "Matches the room visually and your text preference." if tq else "Strong visual similarity to the room."
        elif model_type == "structured":
            parts = []
            if parsed_info:
                if parsed_info.get("color"):
                    parts.append(f"color: {parsed_info['color']}")
                if parsed_info.get("style"):
                    parts.append(f"style: {parsed_info['style']}")
                if parsed_info.get("size"):
                    parts.append(f"size: {parsed_info['size']}")
                if parsed_info.get("shape"):
                    parts.append(f"shape: {parsed_info['shape']}")
            why_text = "Matched on " + ", ".join(parts) if parts else "Matches your structured query."
        else:
            why_text = "Matches your text query semantically."

        item = {
            "title": title,
            "price": price,
            "score": score,
            "image": image_url,
            "model": model_type.upper(),
            "why": why_text,
        }

        output.append(item)

    print("JSON OUTPUT SENT TO FRONTEND:")
    print(output)
    print("==============================\n")

    # Clean up temp image
    if temp_path and os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except Exception:
            pass

    return {"results": output, "parsed_query": parsed_info}
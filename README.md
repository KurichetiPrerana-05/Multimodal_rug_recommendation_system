#  Rug Multimodal Search Engine

A full-stack AI-powered rug recommendation system that combines **visual search**, **semantic text search**, and **structured query parsing** to help users find the perfect rug — either by describing what they want, uploading a room photo, or both.

---

## 📌 Table of Contents

- [What This Project Does](#what-this-project-does)
- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [File-by-File Explanation](#file-by-file-explanation)
- [Setup & Installation](#setup--installation)
- [Running the Project](#running-the-project)
- [API Reference](#api-reference)
- [Search Modes Explained](#search-modes-explained)
- [Fusion Strategy & Weight Justification](#fusion-strategy--weight-justification)

---

## 🔍 What This Project Does

This project is a **multimodal rug search engine** with three distinct search capabilities:

| Mode | Input | How it works |
|------|-------|--------------|
| **CLIP** | Room image + optional text | Encodes image with CLIP, fuses with text similarity |
| **SBERT** | Text query only | Pure semantic similarity using sentence embeddings |
| **Structured** | Natural language text | Parses size, color, style, shape → filters + ranks |

A user can:
- Upload a photo of their living room and get rugs that visually match
- Type "8x10 beige traditional rug" and get rugs filtered by those exact attributes
- Combine both — upload a room photo AND type "modern neutral" for fused results
- Filter results by price range at any time

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (React)                           │
│                                                                     │
│   ┌──────────────┐   ┌──────────────┐   ┌────────────────────────┐ │
│   │  Room Image  │   │  Text Query  │   │  Price Filter / Top-K  │ │
│   │   Upload     │   │   Input      │   │  Model Type Selector   │ │
│   └──────┬───────┘   └──────┬───────┘   └────────────┬───────────┘ │
│          └──────────────────┴────────────────────────┘             │
│                             │ FormData (POST)                       │
└─────────────────────────────┼───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND (api.py)                       │
│                                                                     │
│   POST /search/multimodal                                           │
│   ├── model_type = "clip"       ──► MultimodalSearchEngine          │
│   ├── model_type = "sbert"      ──► MultimodalSearchEngine          │
│   └── model_type = "structured" ──► StructuredSearchEngine          │
│                                                                     │
│   Static files served at /images/*                                  │
└──────────┬────────────────────────────┬────────────────────────────┘
           │                            │
           ▼                            ▼
┌──────────────────────┐   ┌────────────────────────────────────────┐
│  MultimodalSearch    │   │        StructuredSearchEngine          │
│  Engine              │   │                                        │
│                      │   │  ┌─────────────────────────────────┐   │
│  ┌────────────────┐  │   │  │         query_parser.py         │   │
│  │  CLIP Model    │  │   │  │                                 │   │
│  │ (ViT-B/32)     │  │   │  │  Input: "8x10 beige modern rug" │   │
│  │                │  │   │  │                                 │   │
│  │ Image → 512d   │  │   │  │  Regex  ──► size: "8x10"        │   │
│  │ Text  → 512d   │  │   │  │  Rules  ──► shape: None         │   │
│  └────────┬───────┘  │   │  │  spaCy  ──► tokens: [beige,     │   │
│           │          │   │  │                      modern]    │   │
│  ┌────────▼───────┐  │   │  │  SBERT  ──► style: "modern"     │   │
│  │  SBERT Model   │  │   │  │  Logic  ──► color: "beige"      │   │
│  │ (MiniLM-L6-v2) │  │   │  └──────────────┬────────────────┘   │
│  │                │  │   │                 │                      │
│  │ Text → 384d    │  │   │  metadata_match_score()               │
│  └────────┬───────┘  │   │  0.7 × semantic + 0.3 × metadata     │
│           │          │   └────────────────────────────────────────┘
│  Cosine Similarity   │
│  In-Memory Search    │
│                      │
│  Final Score:        │
│  0.6×img + 0.4×text  │
└──────────┬───────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       CATALOG (512 rows)                            │
│                                                                     │
│   load_catalog.py                                                   │
│   ├── Reads data/catalog.csv                                        │
│   ├── Normalizes columns (Title, description, image, price)         │
│   ├── Forward-fills prices across variant rows                      │
│   └── Drops rows with missing/zero prices                           │
│                                                                     │
│   data/rugs/*.jpg  ◄── Local image files referenced by catalog     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
rug-multimodal-search/
│
├── api.py                        # FastAPI backend — main entry point
├── load_catalog.py               # Catalog CSV loader and cleaner
│
├── search/
│   ├── __init__.py
│   ├── multimodal_search.py      # CLIP + SBERT search engine
│   ├── structured_search.py      # Structured query search engine
│   └── query_parser.py           # NLP query parser (size, color, style, shape)
│
├── data/
│   ├── catalog.csv               # Raw product catalog from Shopify export
│   ├── rugs/                     # Downloaded rug images (*.jpg)
│   └── _temp_query.jpg           # Temporary file for uploaded room images
│
├── requirements.txt
└── README.md
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend Framework** | FastAPI | REST API, file uploads, static file serving |
| **ASGI Server** | Uvicorn | Runs the FastAPI app |
| **Image Embeddings** | CLIP (`openai/clip-vit-base-patch32`) | Encodes room images and product images into 512-dim vectors |
| **Text Embeddings** | SBERT (`all-MiniLM-L6-v2`) | Encodes text queries and catalog descriptions into 384-dim vectors |
| **NLP Parsing** | spaCy (`en_core_web_sm`) | POS tagging for color/style extraction |
| **Semantic Matching** | SentenceTransformers + cosine similarity | Style detection, semantic search |
| **Vector Search** | scikit-learn cosine similarity (in-memory) | Fast similarity search over catalog embeddings |
| **Data** | pandas | Catalog loading, cleaning, filtering |
| **Deep Learning Runtime** | PyTorch | Model inference for CLIP |
| **Frontend** | React (separate) | UI for search interface |

---

## 📄 File-by-File Explanation

### `load_catalog.py`

Responsible for loading and cleaning the raw Shopify product CSV export.

**What it does:**
- Reads `data/catalog.csv`
- Keeps only relevant columns: `Handle`, `Title`, `description`, `image`, `price`
- Renames `Body (HTML)` → `description` and `Variant Price` → `price` if needed
- Converts price to numeric and **forward-fills missing prices** across variant rows (Shopify exports only put price on the first variant row; subsequent size variants have blank prices)
- Drops any rows where price is still missing or zero after forward-fill
- Returns a clean DataFrame of 512 rows ready for search

**Key fix — why forward-fill matters:**
Shopify CSVs export one row per product variant (size). Only the first row has a Title and price. Without `ffill()`, all size variants except the first show ₹0.

---

### `search/query_parser.py`

Parses a natural language rug query into structured attributes.

**What it extracts:**

| Attribute | Method | Example |
|-----------|--------|---------|
| `size` | Regex (`\d+x\d+` or `\d+ft`) | `"8x10"`, `"6ft"` |
| `shape` | Rule-based keyword match | `"round"`, `"runner"` |
| `style` | Semantic SBERT similarity vs style concepts | `"modern"`, `"traditional"` |
| `color` | spaCy POS tags + heuristics | `"beige"`, `"navy blue"` |

**How color extraction works:**
1. First tries two-word color phrases (e.g. "navy blue", "light grey") that appear before the word "rug"
2. Falls back to single adjective/noun tokens, skipping generic words, shape words, style words, and size units

**Style detection:**
Encodes each token against a list of style concept embeddings (`"modern style"`, `"traditional style"`, etc.) and picks the best cosine match above a 0.6 threshold.

---

### `search/structured_search.py`

Search engine for structured/parsed text queries.

**Pipeline:**
1. Calls `parse_query()` to extract `{size, color, style, shape}`
2. Encodes the full query with SBERT for semantic similarity
3. For each catalog row, computes:
   - **Semantic score**: cosine similarity between query embedding and title+description embedding
   - **Metadata score**: checks if color, style, shape, size appear in the product text
4. Final score = `0.7 × semantic_score + 0.3 × metadata_score`
5. Applies price filtering (excludes zero/null prices, respects min/max price)
6. Returns top-K results with parsed query info

**Metadata scoring weights:**

| Match | Score |
|-------|-------|
| Color match | +1.0 |
| Style match | +1.0 |
| Shape match | +0.5 |
| Size match | +0.5 |

---

### `search/multimodal_search.py`

Search engine for image-based and pure semantic text queries.

**Initialization (runs once at startup):**
- Loads CLIP model (`openai/clip-vit-base-patch32`)
- Loads SBERT model (`all-MiniLM-L6-v2`)
- Builds and caches **CLIP image embeddings** for all 512 catalog images
- Builds and caches **SBERT text embeddings** for all catalog title+description texts

**`search_clip(room_image_path, text_query, ...)`**
1. Encodes the uploaded room image with CLIP → 512-dim vector
2. If text query provided, encodes it with CLIP text encoder → 512-dim vector
3. For each catalog item, computes cosine similarity between room image and product image
4. If text provided, also computes text-to-product-title similarity
5. Final score = `0.6 × image_similarity + 0.4 × text_similarity`
6. Applies price filtering and returns top-K

**`search_sbert(text_query, ...)` / `search_text_only(...)`**
1. Encodes the text query with SBERT
2. Computes cosine similarity against all pre-cached catalog text embeddings
3. Applies price filtering and returns top-K

**Price filtering (`_apply_price_filter`, `_is_valid_price`):**
Items with missing, NaN, or zero prices are assigned score `-1e9` so they never appear in results.

---

### `api.py`

The FastAPI backend that ties everything together.

**Startup:**
- Loads and cleans the catalog via `load_catalog.py`
- Initializes both `MultimodalSearchEngine` and `StructuredSearchEngine`
- Mounts `data/rugs/` as static files at `/images/*` so the frontend can load rug images

**`POST /search/multimodal`**

Accepts a `multipart/form-data` request with:

| Field | Type | Description |
|-------|------|-------------|
| `image` | File (optional) | Room photo uploaded by user |
| `text_query` | string (optional) | Natural language search query |
| `model_type` | string | `"clip"`, `"sbert"`, or `"structured"` |
| `top_k` | int | Number of results (default 5) |
| `max_price` | float (optional) | Maximum price filter |
| `min_price` | float (optional) | Minimum price filter |

Routes the request to the correct engine, builds a JSON response with title, price, score, image URL, model name, and a human-readable "why" explanation for each result.

---

## ⚙️ Setup & Installation

### Prerequisites

- Python 3.9+
- pip
- Node.js (for React frontend, if applicable)

### 1. Clone the repository

```bash
git clone https://github.com/your-username/rug-multimodal-search.git
cd rug-multimodal-search
```

### 2. Create and activate a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install fastapi uvicorn python-multipart
pip install torch torchvision
pip install transformers
pip install sentence-transformers
pip install scikit-learn
pip install pandas numpy pillow
pip install spacy
pip install aiofiles
```

Or if you have a `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 4. Download the spaCy language model

```bash
python -m spacy download en_core_web_sm
```

### 5. Verify your data directory

Make sure the following exist:

```
data/
├── catalog.csv        # Shopify product export with 'image' column of local paths
└── rugs/              # Folder containing all downloaded rug images
    ├── 0000_palace_10301_....jpg
    ├── 0001_palace_10301_....jpg
    └── ...
```

---

## 🚀 Running the Project

### Start the backend

```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

You should see:

```
Loading catalog and models...
Loading CLIP model (openai/clip-vit-base-patch32)...
Loading SBERT model (all-MiniLM-L6-v2)...
Building image embeddings for catalog (CLIP)...
Building text embeddings for catalog (SBERT)...
Building structured search text embeddings for catalog...
Backend ready.
INFO: Uvicorn running on http://0.0.0.0:8000
```

> ⚠️ First startup takes 1–3 minutes to build all embeddings. Subsequent starts are faster if embeddings are cached.

### Test the API directly

```bash
# Text-only SBERT search
curl -X POST http://localhost:8000/search/multimodal \
  -F "text_query=beige modern rug" \
  -F "model_type=sbert" \
  -F "top_k=5"

# Structured search with price filter
curl -X POST http://localhost:8000/search/multimodal \
  -F "text_query=8x10 navy blue traditional rug" \
  -F "model_type=structured" \
  -F "max_price=500" \
  -F "top_k=5"

# CLIP image + text search
curl -X POST http://localhost:8000/search/multimodal \
  -F "image=@/path/to/your/room.jpg" \
  -F "text_query=modern neutral" \
  -F "model_type=clip" \
  -F "top_k=5"
```

### Test the query parser standalone

```bash
python search/query_parser.py
```

Expected output:

```
8x10 beige modern rug -> {'size': '8x10', 'color': 'beige', 'style': 'modern', 'shape': None}
round 6 ft maroon traditional rug -> {'size': '6ft', 'color': 'maroon', 'style': 'traditional', 'shape': 'round'}
runner 2x10 teal rug -> {'size': '2x10', 'color': 'teal', 'style': None, 'shape': 'runner'}
large charcoal rug -> {'size': None, 'color': 'charcoal', 'style': None, 'shape': None}
navy blue vintage rug -> {'size': None, 'color': 'navy blue', 'style': 'vintage', 'shape': None}
```

### Test catalog loading standalone

```bash
python load_catalog.py
```

---

## 📡 API Reference

### `POST /search/multimodal`

**Content-Type:** `multipart/form-data`

**Request Fields:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `model_type` | string | No | `"clip"` | `"clip"`, `"sbert"`, or `"structured"` |
| `image` | file | Required for CLIP | — | Room photo (jpg/png) |
| `text_query` | string | Required for SBERT/structured | — | Natural language query |
| `top_k` | int | No | `5` | Number of results to return |
| `max_price` | float | No | — | Maximum price filter |
| `min_price` | float | No | — | Minimum price filter |

**Response:**

```json
{
  "results": [
    {
      "title": "Palace 10301 Beige/Grey Oriental Rug",
      "price": 299.5,
      "score": 0.812,
      "image": "/images/0000_palace_10301_....jpg",
      "model": "CLIP",
      "why": "Matches the room visually and your text preference."
    }
  ],
  "parsed_query": {
    "size": "8x10",
    "color": "beige",
    "style": "modern",
    "shape": null
  }
}
```

> `parsed_query` is only populated for `model_type="structured"`, `null` otherwise.

### `GET /images/{filename}`

Serves static rug images from `data/rugs/`. Used by the frontend to display rug thumbnails.

---

## 🔍 Search Modes Explained

### Mode 1: CLIP (Multimodal)

The user uploads a room photo. CLIP encodes the room image into a 512-dimensional vector that captures visual features — colors, patterns, lighting, style. Each catalog rug image is also encoded at startup and cached. Cosine similarity is computed between the room vector and all rug vectors.

If a text query is also provided (e.g. "modern neutral"), CLIP encodes the text into the same 512-dim space and the final score fuses both signals.

### Mode 2: SBERT (Semantic Text)

The user types a description. SBERT encodes the query and all catalog title+description texts into a shared 384-dim semantic space. Results are ranked purely by semantic similarity — so "cozy warm rug" will match products described as "earthy tones" even without exact keyword overlap.

### Mode 3: Structured Query

The user types something like "8x10 navy blue Persian rug". The query parser extracts:
- Size via regex
- Shape via keyword rules
- Style via semantic matching to known style concepts
- Color via POS tagging and heuristics

Results are ranked by a blend of semantic similarity (70%) and how many extracted attributes match the product (30%).

---

## ⚖️ Fusion Strategy & Weight Justification

### CLIP Fusion (image + text)

```
Final Score = 0.6 × image_similarity + 0.4 × text_similarity
```

**Why 0.6 / 0.4?**
The primary use case for CLIP mode is visual matching — a user uploads their room and wants rugs that look right in that space. Color, texture, pattern, and visual style are best captured by image-to-image similarity. Text acts as a refinement signal ("I like what I see but I also want something modern"), so it gets a lower weight. If no text is provided, the full score comes from image similarity alone (weight becomes 1.0 implicitly).

### Structured Query Fusion (semantic + metadata)

```
Final Score = 0.7 × semantic_similarity + 0.3 × metadata_score
```

**Why 0.7 / 0.3?**
Semantic similarity captures the overall intent of the query and handles synonyms and paraphrasing well. Metadata scoring acts as a boosting signal — if a product explicitly mentions the color or size the user asked for, it should rank higher, but not so much higher that semantically irrelevant products with matching keywords beat genuinely relevant ones.
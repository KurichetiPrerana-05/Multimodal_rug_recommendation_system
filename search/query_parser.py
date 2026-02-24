
import re
import spacy
from sentence_transformers import SentenceTransformer, util

# Load NLP model
nlp = spacy.load("en_core_web_sm")

# Embedding model (used only for style detection)
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

# Style concepts (for semantic matching)
STYLE_CONCEPTS = [
    "modern style", "traditional style", "persian style", "vintage style",
    "bohemian style", "minimal style", "contemporary style", "classic style",
    "abstract style", "oriental style"
]
style_embs = embed_model.encode(STYLE_CONCEPTS)

# Known shape words
SHAPE_WORDS = ["round", "runner", "square", "rectangle", "rectangular", "oval"]

# Generic words to ignore for color/descriptor
GENERIC_WORDS = set([
    "rug", "rugs", "carpet", "carpets", "area", "for", "with", "and", "the",
    "a", "an", "large", "small", "medium", "room", "living", "dining"
])

SIZE_UNITS = ["ft", "feet", "foot"]

# Color synonyms/variants for better matching
COLOR_SYNONYMS = {
    "grey": ["grey", "gray"],
    "gray": ["grey", "gray"],
    "beige": ["beige", "cream", "ivory"],
    "navy": ["navy", "navy blue"],
    "navy blue": ["navy", "navy blue"],
    "off white": ["off white", "offwhite", "ivory", "cream"],
    "offwhite": ["off white", "offwhite", "ivory", "cream"],
    "cream": ["cream", "ivory", "beige", "off white"],
    "ivory": ["ivory", "cream", "off white"],
    "charcoal": ["charcoal", "dark grey", "dark gray"],
    "teal": ["teal", "turquoise"],
    "turquoise": ["teal", "turquoise"],
    "maroon": ["maroon", "burgundy", "wine"],
    "burgundy": ["maroon", "burgundy", "wine"],
}


def expand_color(color):
    """Return list of color variants to match against catalog text."""
    if color is None:
        return []
    c = color.lower().strip()
    return COLOR_SYNONYMS.get(c, [c])


def extract_size(text):
    size = None
    m = re.search(r"(\d+)\s*[x×]\s*(\d+)", text)
    if m:
        size = f"{m.group(1)}x{m.group(2)}"
    else:
        m2 = re.search(r"(\d+)\s*(ft|feet|foot)", text)
        if m2:
            size = m2.group(1) + "ft"
    return size


def best_style_match(word):
    w_emb = embed_model.encode([word])[0]
    sims = util.cos_sim(w_emb, style_embs)[0]
    best_idx = sims.argmax().item()
    best_score = sims[best_idx].item()
    return STYLE_CONCEPTS[best_idx], best_score


def is_size_like(token):
    return bool(re.search(r"\d", token))


def parse_query(query: str):
    q = query.lower()
    doc = nlp(q)

    # 1. Size
    size = extract_size(q)

    # 2. Shape
    shape = None
    for sh in SHAPE_WORDS:
        if sh in q:
            shape = sh
            break

    # 3. Collect descriptive tokens
    tokens = [t for t in doc if t.pos_ in ["ADJ", "NOUN"]]

    # 4. Style (semantic match)
    style = None
    for tok in tokens:
        concept, score = best_style_match(tok.text.lower())
        if score > 0.6:
            style = concept.replace(" style", "")
            break

    # 5. Color — try two-word phrases first, then single word
    color = None
    words = [t.text.lower() for t in doc]

    for i in range(len(words) - 1):
        w1, w2 = words[i], words[i + 1]
        if w1 in SIZE_UNITS or w2 in SIZE_UNITS:
            continue
        if not w1.isalpha() or not w2.isalpha():
            continue
        if w1 in GENERIC_WORDS or w2 in GENERIC_WORDS:
            continue
        if w1 in SHAPE_WORDS or w2 in SHAPE_WORDS:
            continue
        if style and (w1 in style or w2 in style):
            continue
        if is_size_like(w1) or is_size_like(w2):
            continue
        if "rug" in words:
            rug_index = words.index("rug")
            if i < rug_index:
                color = f"{w1} {w2}"
                break
        else:
            color = f"{w1} {w2}"
            break

    if color is None:
        for tok in tokens:
            w = tok.text.lower()
            if w in GENERIC_WORDS:
                continue
            if w in SHAPE_WORDS:
                continue
            if style and w in style:
                continue
            if w in SIZE_UNITS:
                continue
            if is_size_like(w):
                continue
            color = w
            break

    return {
        "size": size,
        "color": color,
        "style": style,
        "shape": shape
    }


if __name__ == "__main__":
    tests = [
        "8x10 beige modern rug",
        "round 6 ft maroon traditional rug",
        "runner 2x10 teal rug",
        "large charcoal rug",
        "navy blue vintage rug",
        "minimal neutral rug for living room",
        "light grey modern rug",
        "dark brown traditional rug",
        "grey round rug",
        "round grey rug",
    ]
    for t in tests:
        print(t, "->", parse_query(t))
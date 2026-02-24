
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from search.query_parser import parse_query, expand_color


class StructuredSearchEngine:
    def __init__(self, catalog_df):
        self.catalog = catalog_df.reset_index(drop=True)
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

        texts = (
            self.catalog["Title"].fillna("") + " " +
            self.catalog["description"].fillna("")
        ).tolist()

        print("Building structured search text embeddings for catalog...")
        self.text_embeddings = self.model.encode(texts, show_progress_bar=True)

    def metadata_match_score(self, row, parsed):
        score = 0.0
        text = (str(row.get("Title", "")) + " " + str(row.get("description", ""))).lower()

        # Color — heavily weighted, penalize mismatches
        if parsed["color"]:
            color_variants = expand_color(parsed["color"])
            matched = any(c in text for c in color_variants)
            if matched:
                score += 3.0
            else:
                score -= 2.0  # penalize wrong color

        # Shape — very specific filter, high boost
        if parsed["shape"]:
            if parsed["shape"].lower() in text:
                score += 1.5
            else:
                score -= 1.0  # penalize wrong shape

        # Style
        if parsed["style"] and parsed["style"].lower() in text:
            score += 1.0

        # Size
        if parsed["size"] and parsed["size"].lower() in text:
            score += 0.5

        return score

    def _is_valid_price(self, price):
        try:
            return price is not None and not pd.isna(price) and float(price) > 0
        except Exception:
            return False

    def search(self, query, top_k=10, max_price=None, min_price=None):
        parsed = parse_query(query)
        print("Parsed query:", parsed)

        # Semantic similarity
        query_emb = self.model.encode([query])
        sims = cosine_similarity(query_emb, self.text_embeddings)[0]

        # If color or shape explicitly given, metadata should dominate over semantics
        has_specific_filter = bool(parsed["color"] or parsed["shape"])
        w_semantic = 0.3 if has_specific_filter else 0.7
        w_metadata = 0.7 if has_specific_filter else 0.3

        print(f"Fusion weights — semantic: {w_semantic}, metadata: {w_metadata}")

        scores = []
        for i, row in self.catalog.iterrows():
            price = row.get("price", None)

            if not self._is_valid_price(price):
                scores.append(-1e9)
                continue

            price = float(price)

            if max_price is not None and price > max_price:
                scores.append(-1e9)
                continue
            if min_price is not None and price < min_price:
                scores.append(-1e9)
                continue

            meta_score = self.metadata_match_score(row, parsed)
            final_score = w_semantic * sims[i] + w_metadata * meta_score
            scores.append(final_score)

        scores = np.array(scores)
        top_idx = scores.argsort()[::-1][:top_k]

        results = self.catalog.iloc[top_idx].copy()
        results["score"] = scores[top_idx]
        results["parsed_query"] = str(parsed)

        return results, parsed
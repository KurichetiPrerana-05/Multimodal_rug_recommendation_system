import os
import numpy as np
import torch
import pandas as pd
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class MultimodalSearchEngine:
    def __init__(self, catalog_df):
        self.catalog = catalog_df.reset_index(drop=True)

        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        print("Loading CLIP model (openai/clip-vit-base-patch32)...")
        self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(self.device)
        self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

        print("Loading SBERT model (all-MiniLM-L6-v2)...")
        self.sbert_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

        print("Building image embeddings for catalog (CLIP)...")
        self.image_embeddings = self._build_image_embeddings()

        print("Building text embeddings for catalog (SBERT)...")
        self.text_embeddings = self._build_text_embeddings()

    def _load_image(self, path):
        try:
            return Image.open(path).convert("RGB")
        except Exception as e:
            print(f"⚠️ Could not load image: {path} ({e})")
            return None

    def _encode_image_clip(self, img: Image.Image):
        inputs = self.clip_processor(images=img, return_tensors="pt")
        pixel_values = inputs["pixel_values"].to(self.device)

        with torch.no_grad():
            feats = self.clip_model.get_image_features(pixel_values=pixel_values)

        if not isinstance(feats, torch.Tensor):
            feats = feats.image_embeds if hasattr(feats, "image_embeds") else feats.pooler_output

        feats = feats / feats.norm(dim=-1, keepdim=True)
        return feats.cpu().numpy()[0]

    def _encode_text_clip(self, text: str):
        inputs = self.clip_processor(
            text=[text],
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=77
        )

        input_ids = inputs["input_ids"].to(self.device)
        attention_mask = inputs["attention_mask"].to(self.device)

        with torch.no_grad():
            feats = self.clip_model.get_text_features(
                input_ids=input_ids,
                attention_mask=attention_mask
            )

        if not isinstance(feats, torch.Tensor):
            feats = feats.text_embeds if hasattr(feats, "text_embeds") else feats.pooler_output

        feats = feats / feats.norm(dim=-1, keepdim=True)
        return feats.cpu().numpy()[0]

    def _encode_text_sbert(self, texts):
        return self.sbert_model.encode(texts, normalize_embeddings=True)

    def _build_image_embeddings(self):
        embeddings = []

        for idx, row in self.catalog.iterrows():
            img_path = row.get("image", None)

            if not isinstance(img_path, str) or not os.path.exists(img_path):
                embeddings.append(None)
                continue

            img = self._load_image(img_path)
            if img is None:
                embeddings.append(None)
                continue

            try:
                emb = self._encode_image_clip(img)
                embeddings.append(emb)
            except Exception as e:
                print(f"⚠️ CLIP image encoding failed for {img_path}: {e}")
                embeddings.append(None)

        return embeddings

    def _build_text_embeddings(self):
        texts = []
        for _, row in self.catalog.iterrows():
            title = str(row.get("Title", ""))
            desc = str(row.get("description", ""))
            combined = (title + " " + desc).strip()
            texts.append(combined if combined else "rug")

        embeddings = self._encode_text_sbert(texts)
        return embeddings

    def _is_valid_price(self, price):
        try:
            return price is not None and not pd.isna(price) and float(price) > 0
        except Exception:
            return False

    def _apply_price_filter(self, sims, max_price=None, min_price=None):
        sims = sims.copy()
        for i in range(len(sims)):
            price = self.catalog.iloc[i].get("price", None)

            if not self._is_valid_price(price):
                sims[i] = -1e9
                continue

            price = float(price)
            if max_price is not None and price > max_price:
                sims[i] = -1e9
            if min_price is not None and price < min_price:
                sims[i] = -1e9

        return sims

    def search_text_only(self, text_query, top_k=5, max_price=None, min_price=None):
        query_emb = self._encode_text_sbert([text_query])[0].reshape(1, -1)
        sims = cosine_similarity(self.text_embeddings, query_emb).squeeze()
        sims = self._apply_price_filter(sims, max_price, min_price)
        top_idx = sims.argsort()[::-1][:top_k]
        results = self.catalog.iloc[top_idx].copy()
        results["score"] = sims[top_idx]
        return results

    def search_sbert(self, text_query, top_k=5, max_price=None, min_price=None):
        return self.search_text_only(text_query, top_k=top_k, max_price=max_price, min_price=min_price)

    def search_clip(self, room_image_path, text_query=None, top_k=5, w_image=0.6, w_text=0.4, max_price=None, min_price=None):
        room_img = Image.open(room_image_path).convert("RGB")
        room_feat = self._encode_image_clip(room_img).reshape(1, -1)

        if text_query:
            text_feat = self._encode_text_clip(text_query).reshape(1, -1)
        else:
            text_feat = None

        scores = []

        for i, img_emb in enumerate(self.image_embeddings):
            if img_emb is None:
                scores.append(-1e9)
                continue

            price = self.catalog.iloc[i].get("price", None)

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

            img_emb = img_emb.reshape(1, -1)
            img_sim = cosine_similarity(room_feat, img_emb)[0][0]

            if text_feat is not None:
                prod_text = str(self.catalog.iloc[i].get("Title", ""))
                prod_text_feat = self._encode_text_clip(prod_text).reshape(1, -1)
                text_sim = cosine_similarity(text_feat, prod_text_feat)[0][0]
                final_score = w_image * img_sim + w_text * text_sim
            else:
                final_score = img_sim

            scores.append(final_score)

        scores = np.array(scores)
        top_idx = scores.argsort()[::-1][:top_k]
        results = self.catalog.iloc[top_idx].copy()
        results["score"] = scores[top_idx]
        return results